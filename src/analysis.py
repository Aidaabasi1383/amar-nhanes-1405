"""
Phase 1 analysis helpers for the NHANES 2021-2023 project
(Statistics & Applications course, Fall 1405).

Research question (working version, Phase 1):
Is mean oscillometric systolic blood pressure associated with usual sleep
duration, sedentary time, smoking status and BMI among U.S. adults aged
20+ in NHANES 2021-2023?

All functions are pure / side-effect-light so they can be called both from
the exploration notebook and from the report-building script, keeping the
two artifacts in sync with a single source of truth.
"""
from __future__ import annotations

import pandas as pd
import numpy as np
from pathlib import Path

RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"
PROCESSED_DIR = Path(__file__).resolve().parents[1] / "data" / "processed"

FILES = ["DEMO_L", "BPXO_L", "BMX_L", "SLQ_L", "PAQ_L", "SMQ_L"]

# NHANES refused/don't-know sentinel codes that must be recoded to missing
# for the specific variables we use in this project.
MISSING_CODES = {
    "PAD680": [7777, 9999],
    "SMQ040": [7, 9],
    "SMQ020": [7, 9],
    "DMDEDUC2": [7, 9],
}


def load_raw() -> dict[str, pd.DataFrame]:
    """Read the six NHANES 2021-2023 XPT files downloaded from the CDC site."""
    out = {}
    for f in FILES:
        out[f] = pd.read_sas(RAW_DIR / f"{f}.xpt", format="xport")
    return out


def merge_and_clean() -> tuple[pd.DataFrame, dict]:
    """Merge the six component files on SEQN, apply inclusion/exclusion
    criteria for the analytic population, and build derived variables.

    Returns the cleaned analytic DataFrame and a dict with merge / filtering
    counts used for the reproducibility narrative (task Al.1 / Al.4).
    """
    raw = load_raw()
    counts = {"raw_rows": {k: len(v) for k, v in raw.items()}}

    # DEMO_L is the base file: every NHANES participant has a DEMO_L row.
    df = raw["DEMO_L"].copy()
    counts["n_demo_base"] = len(df)

    for f in ["BPXO_L", "BMX_L", "SLQ_L", "PAQ_L", "SMQ_L"]:
        before = len(df)
        df = df.merge(raw[f], on="SEQN", how="left")
        counts[f"n_after_merge_{f}"] = len(df)
        assert len(df) == before, "merge on SEQN must be 1:1 (unique key)"

    counts["n_merged_total"] = len(df)
    counts["duplicate_seqn"] = int(df["SEQN"].duplicated().sum())

    # --- recode refused / don't know sentinel codes to missing -------------
    for col, codes in MISSING_CODES.items():
        df.loc[df[col].isin(codes), col] = np.nan

    # --- derived variables ---------------------------------------------
    sbp_cols = ["BPXOSY1", "BPXOSY2", "BPXOSY3"]
    dbp_cols = ["BPXODI1", "BPXODI2", "BPXODI3"]
    df["sbp_mean"] = df[sbp_cols].mean(axis=1, skipna=True)
    df["dbp_mean"] = df[dbp_cols].mean(axis=1, skipna=True)
    df["n_bp_readings"] = df[sbp_cols].notna().sum(axis=1)

    df["sex"] = df["RIAGENDR"].map({1: "Male", 2: "Female"})
    df["age_years"] = df["RIDAGEYR"]
    df["sleep_hours"] = df["SLD012"]
    df["sedentary_min"] = df["PAD680"]
    df["bmi"] = df["BMXBMI"]

    df["smoking_status"] = np.select(
        [df["SMQ020"] == 2, df["SMQ040"] == 1, df["SMQ040"] == 2, df["SMQ040"] == 3],
        ["Never smoker", "Current, every day", "Current, some days", "Former smoker"],
        default="__NA__",
    )
    df.loc[df["smoking_status"] == "__NA__", "smoking_status"] = np.nan
    df["smoker_group"] = np.where(
        df["smoking_status"].isin(["Current, every day", "Current, some days"]),
        "Current smoker",
        np.where(df["smoking_status"].isna(), "__NA__", "Non-current smoker"),
    )
    df.loc[df["smoker_group"] == "__NA__", "smoker_group"] = np.nan

    educ_map = {
        1: "<9th grade", 2: "9-11th grade", 3: "HS grad/GED",
        4: "Some college/AA", 5: "College grad+",
    }
    df["education"] = df["DMDEDUC2"].map(educ_map)

    df["age_group"] = pd.cut(
        df["age_years"], bins=[19, 39, 59, np.inf],
        labels=["20-39", "40-59", "60+"], right=True,
    )

    # --- inclusion / exclusion criteria (task Al.4) ---------------------
    counts["n_before_filters"] = len(df)

    mask_examined = df["RIDSTATR"] == 2
    counts["excluded_not_mec_examined"] = int((~mask_examined).sum())

    mask_adult = df["RIDAGEYR"] >= 20
    counts["excluded_under_20"] = int((mask_examined & ~mask_adult).sum())

    mask_not_pregnant = df["RIDEXPRG"] != 1.0
    counts["excluded_pregnant"] = int(
        (mask_examined & mask_adult & ~mask_not_pregnant).sum()
    )

    mask_has_bp = df["n_bp_readings"] >= 1
    counts["excluded_no_valid_bp"] = int(
        (mask_examined & mask_adult & mask_not_pregnant & ~mask_has_bp).sum()
    )

    keep = mask_examined & mask_adult & mask_not_pregnant & mask_has_bp
    analytic = df.loc[keep].copy()
    counts["n_analytic_sample"] = len(analytic)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    keep_cols = [
        "SEQN", "sex", "age_years", "age_group", "education",
        "sbp_mean", "dbp_mean", "n_bp_readings", "bmi", "sleep_hours",
        "sedentary_min", "smoking_status", "smoker_group",
        "WTMEC2YR", "WTINT2YR", "SDMVSTRA", "SDMVPSU",
    ]
    analytic[keep_cols].to_csv(PROCESSED_DIR / "phase1_analytic.csv", index=False)

    return analytic, counts


def data_quality_report(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    """Missing-value audit for a chosen set of analytic variables."""
    rows = []
    for c in cols:
        n_missing = df[c].isna().sum()
        rows.append({
            "variable": c,
            "n_missing": int(n_missing),
            "pct_missing": round(100 * n_missing / len(df), 2),
            "n_valid": int(df[c].notna().sum()),
        })
    return pd.DataFrame(rows)


def weighted_mean(x: pd.Series, w: pd.Series) -> float:
    mask = x.notna() & w.notna()
    return float(np.average(x[mask], weights=w[mask]))


def weighted_vs_unweighted(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for var in ["sbp_mean", "bmi", "sleep_hours"]:
        unw = df[var].mean()
        w = weighted_mean(df[var], df["WTMEC2YR"])
        rows.append({
            "variable": var,
            "unweighted_mean": round(unw, 2),
            "mec_weighted_mean": round(w, 2),
            "abs_difference": round(abs(unw - w), 2),
        })
    return pd.DataFrame(rows)


def center_spread_table(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    rows = []
    for c in cols:
        s = df[c].dropna()
        rows.append({
            "variable": c,
            "n": len(s),
            "mean": round(s.mean(), 2),
            "sd": round(s.std(), 2),
            "median": round(s.median(), 2),
            "iqr": round(s.quantile(0.75) - s.quantile(0.25), 2),
            "min": round(s.min(), 2),
            "max": round(s.max(), 2),
        })
    return pd.DataFrame(rows)


def group_compare_descriptive(df: pd.DataFrame, value_col: str, group_col: str) -> pd.DataFrame:
    """Purely descriptive group comparison (no hypothesis test yet - Phase 1)."""
    g = df.dropna(subset=[value_col, group_col]).groupby(group_col, observed=True)[value_col]
    out = g.agg(n="count", mean="mean", sd="std", median="median").round(2)
    return out.reset_index()
