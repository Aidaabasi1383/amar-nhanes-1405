"""Reproduce the Phase 2 descriptive probability analysis."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
FIGURES = ROOT / "figures" / "phase2"
TABLES = ROOT / "reports" / "phase2"
THRESHOLD = 140
GROUP_SIZE = 20
TRIALS = 10000
SEED = 1405


def analyze():
    df = pd.read_csv(ROOT / "data/processed/phase1_analytic.csv")
    if df.empty or df.SEQN.isna().any() or not df.SEQN.is_unique:
        raise ValueError("Expected one row per participant in the Phase 1 analytic CSV.")
    if not np.isfinite(df.sbp_mean).all():
        raise ValueError("The Phase 1 cohort must have valid systolic BP for every row.")
    high = df.sbp_mean.ge(THRESHOLD)
    known = df.smoker_group.isin(["Current smoker", "Non-current smoker"])
    current = df.smoker_group.eq("Current smoker")
    cross = pd.crosstab(current[known], high[known]).reindex(
        index=[False, True], columns=[False, True], fill_value=0
    )
    cross.index = ["Non-current smoker", "Current smoker"]
    cross.columns = ["SBP < 140", "SBP >= 140"]
    a, b = cross.sum(axis=0).iloc[1], cross.sum(axis=1).iloc[1]
    joint = cross.iloc[1, 1]
    n = int(known.sum())
    p_a, p_b = a / n, b / n
    p_a_b = joint / b
    p = high.mean()

    subgroups = []
    for field in ["age_group", "sex"]:
        for group, rows in df.assign(high=high).groupby(field, sort=False):
            subgroups.append((field, group, len(rows), int(rows.high.sum()), rows.high.mean()))
    subgroups = pd.DataFrame(subgroups, columns=["Variable", "Group", "n", "Cases", "Proportion"])

    if not np.isfinite(df.WTMEC2YR).all() or not df.WTMEC2YR.gt(0).all():
        raise ValueError("Expected positive MEC weights for the complete BP cohort.")
    weighted = np.average(high, weights=df.WTMEC2YR)

    # Independent repetitions of the same within-draw sampling experiment.
    rng = np.random.default_rng(SEED)
    values = high.to_numpy()
    counts = np.array([values[rng.choice(len(df), GROUP_SIZE, replace=False)].sum()
                       for _ in range(TRIALS)])
    k = np.arange(GROUP_SIZE + 1)
    pmf = pd.DataFrame({
        "k": k,
        "Repeated subsamples": np.bincount(counts, minlength=len(k)) / TRIALS,
        "Binomial": stats.binom.pmf(k, GROUP_SIZE, p),
        "Hypergeometric": stats.hypergeom.pmf(k, len(df), int(high.sum()), GROUP_SIZE),
    })

    x = df.sbp_mean
    mean, variance = x.mean(), x.var(ddof=0)
    q1, q3 = x.quantile([.25, .75])
    lower, upper = q1 - 1.5 * (q3 - q1), q3 + 1.5 * (q3 - q1)
    pairs = df[["sleep_hours", "sbp_mean"]].dropna()
    covariance = np.cov(pairs.to_numpy().T, ddof=0)[0, 1]
    measures = {
        "BP cohort n": len(df), "Known smoking n": n, "High SBP count": high.sum(),
        "P(A), known smoking": p_a, "P(B), known smoking": p_b,
        "P(A and B)": joint / n, "P(A)P(B)": p_a * p_b,
        "P(A | B)": p_a_b, "P(A | B complement)": (a - joint) / (n - b),
        "P(B | A), Bayes": p_a_b * p_b / p_a, "P(B | A), direct": joint / a,
        "Unweighted P(A), BP cohort": p, "MEC-weighted P(A), BP cohort": weighted,
        "Bernoulli variance": p * (1 - p), "Binomial mean": GROUP_SIZE * p,
        "Binomial variance": GROUP_SIZE * p * (1 - p),
        "Subsample mean": counts.mean(), "Subsample variance": counts.var(),
        "SBP mean": mean, "SBP variance": variance, "SBP SD": np.sqrt(variance),
        "SBP median": x.median(), "SBP skewness": stats.skew(x, bias=False),
        "Lower Tukey fence": lower, "Upper Tukey fence": upper,
        "Below lower fence": x.lt(lower).sum(), "Above upper fence": x.gt(upper).sum(),
        "Normal P(A)": stats.norm.sf(THRESHOLD, mean, np.sqrt(variance)),
        "Sleep-SBP pairs": len(pairs), "Sleep-SBP covariance": covariance,
    }
    assert np.isclose(measures["P(B | A), Bayes"], joint / a)
    assert np.allclose(pmf.iloc[:, 1:].sum(), 1)
    assert subgroups.groupby("Variable").n.sum().eq(len(df)).all()
    return df, cross, subgroups, pmf, measures, pairs


def plot(df, pmf, m, pairs):
    FIGURES.mkdir(parents=True, exist_ok=True)
    plt.style.use("seaborn-v0_8-whitegrid")
    fig, ax = plt.subplots(figsize=(7.6, 3.4), layout="constrained")
    ax.bar(pmf.k, pmf["Repeated subsamples"], color="#a8d4db", label="Repeated subsamples")
    ax.plot(pmf.k, pmf.Binomial, "o", color="#163d61", label="Binomial PMF")
    ax.plot(pmf.k, pmf.Hypergeometric, "+", color="#b94e29", label="Exact finite-cohort PMF")
    ax.set(xlabel="Number with mean SBP ≥ 140 among 20 adults", ylabel="Probability",
           title="Distribution of counts in equal-size subsamples", xticks=pmf.k[::2])
    ax.legend()
    fig.savefig(FIGURES / "binomial.png", dpi=180)
    plt.close(fig)

    x = df.sbp_mean
    grid = np.linspace(x.min(), x.max(), 400)
    fig, axes = plt.subplots(1, 2, figsize=(8.5, 3.5), layout="constrained")
    ax, qq = axes
    ax.hist(x, bins=35, density=True, color="#a8d4db", label="Empirical")
    ax.plot(grid, stats.norm.pdf(grid, m["SBP mean"], m["SBP SD"]),
            color="#163d61", label="Fitted normal")
    ax.axvline(THRESHOLD, color="#b94e29", linestyle="--", label="140 mmHg")
    ax.set(xlabel="Mean systolic BP (mmHg)", ylabel="Density (1/mmHg)", title="SBP distribution")
    ax.legend(fontsize=8)
    (theory, observed), (slope, intercept, _) = stats.probplot(x)
    qq.scatter(theory, observed, color="#163d61", s=5)
    qq.plot(theory, intercept + slope * theory, color="#b94e29")
    qq.set(xlabel="Standard normal quantiles", ylabel="Observed SBP (mmHg)", title="Normal Q–Q plot")
    fig.savefig(FIGURES / "normal.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7.6, 3.6), layout="constrained")
    ax.scatter(pairs.sleep_hours, pairs.sbp_mean, s=8, alpha=.18, color="#163d61", linewidths=0)
    ax.set(xlabel="Usual weekday sleep (hours)", ylabel="Mean systolic BP (mmHg)",
           title=f"Reported sleep and systolic BP ({len(pairs):,} complete pairs)")
    fig.savefig(FIGURES / "sleep_sbp.png", dpi=180)
    plt.close(fig)


def main():
    df, cross, subgroups, pmf, measures, pairs = analyze()
    TABLES.mkdir(parents=True, exist_ok=True)
    cross.to_csv(TABLES / "event_counts.csv", index_label="Smoking")
    subgroups.to_csv(TABLES / "subgroup_probabilities.csv", index=False)
    pmf.to_csv(TABLES / "count_probabilities.csv", index=False)
    pd.Series(measures, name="Value").to_csv(TABLES / "summary.csv", index_label="Measure")
    plot(df, pmf, measures, pairs)


if __name__ == "__main__":
    main()
