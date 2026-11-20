"""Build the Phase 2 report from the same analysis used for tables and figures."""
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from phase2 import ROOT, FIGURES, analyze, plot


def build():
    df, cross, subgroups, pmf, m, pairs = analyze()
    plot(df, pmf, m, pairs)
    styles = getSampleStyleSheet()
    styles["BodyText"].leading = 15
    styles["BodyText"].spaceAfter = 9
    story = []

    def heading(text):
        story.append(Paragraph(text, styles["Heading1"]))

    def body(text):
        story.append(Paragraph(text, styles["BodyText"]))

    def table(rows, widths):
        t = Table(rows, colWidths=widths)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#163d61")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#ecf3f5"), colors.white]),
            ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.extend([t, Spacer(1, 10)])

    def figure(name, width, height, caption):
        story.append(Image(str(FIGURES / name), width=width, height=height))
        body(caption)

    body("STATISTICS &amp; APPLICATIONS  /  FALL 1405  /  TRACK A")
    story.append(Paragraph("Phase 2<br/>Probability and Distributions", styles["Title"]))
    body("NHANES August 2021 to August 2023")
    heading("1. Events and empirical probabilities")
    body(f"The analysis follows the Phase 1 cohort of {len(df):,} MEC-examined adults aged "
         "20 or older with at least one valid systolic BP reading and no recorded pregnancy "
         "at examination. Each row represents one adult. For a uniform draw from these rows, "
         "X is that adult's mean systolic BP (SBP) in mmHg. A is the event X &ge; 140, used "
         "as an analytical threshold for measured SBP. Clinical diagnosis requires additional "
         "information. B is current cigarette smoking (every day or some days). Former and "
         "never smokers form the comparison group. Smoking calculations exclude "
         f"{len(df) - int(m['Known smoking n'])} rows with unknown status.")
    table([["Smoking status", "SBP < 140", "SBP >= 140", "Total"]]
          + [[idx, *row.tolist(), row.sum()] for idx, row in cross.iterrows()]
          + [["Total", *cross.sum().tolist(), cross.to_numpy().sum()]], [170, 92, 92, 75])
    body(f"Among adults with known smoking status, P(A) = {m['P(A), known smoking']:.4f}, "
         f"P(B) = {m['P(B), known smoking']:.4f}, and P(A and B) = {m['P(A and B)']:.4f}. "
         "The joint probability is the fraction who both currently smoke and meet the SBP threshold.")
    body(f"P(A | B) = {m['P(A | B)']:.2%} and P(A | B complement) = "
         f"{m['P(A | B complement)']:.2%}. The observed difference is "
         f"{100 * (m['P(A | B)'] - m['P(A | B complement)']):.2f} percentage points. "
         f"Under empirical independence, the joint probability would equal P(A)P(B) = "
         f"{m['P(A)P(B)']:.4f}. The two empirical events depart modestly from exact independence. "
         "Age and other covariates may contribute to the crude difference.")
    body(f"Bayes' rule updates the current-smoking fraction from {m['P(B), known smoking']:.2%} "
         f"to P(B | A) = P(A | B)P(B)/P(A) = {m['P(B | A), Bayes']:.2%} once A is known. "
         f"The direct calculation, {cross.iloc[1, 1]}/{cross.iloc[:, 1].sum()}, gives the same value.")

    story.append(PageBreak())
    heading("2. Subgroups and survey weights")
    body("Each subgroup proportion divides the number of adults meeting the threshold by all "
         "adults in that subgroup. This comparison uses the full BP cohort.")
    table([["Group", "Adults", "Cases", "P(A | group)"]] +
          [[row.Group, f"{row.n:,}", row.Cases, f"{row.Proportion:.2%}"]
           for row in subgroups.sort_values(["Variable", "Group"]).itertuples()], [170, 86, 75, 98])
    body("The observed proportion increases across age categories. Male and female fractions "
         "are close in the pooled sample. These are descriptive comparisons without covariate adjustment.")
    body(f"The full-cohort proportion is {int(m['High SBP count']):,}/{len(df):,} = "
         f"{m['Unweighted P(A), BP cohort']:.2%}. The ratio sum(w × I(A))/sum(w), using the MEC "
         f"exam weight WTMEC2YR for the same adults, is {m['MEC-weighted P(A), BP cohort']:.2%}. "
         "The weight reflects unequal selection probabilities and survey adjustments, so a "
         "weighted estimate and a row fraction can differ. The result applies to the defined "
         "analytic domain and may still be affected by missing BP and the cohort exclusions. "
         "Strata and clusters would enter design-based uncertainty calculations in a later phase.")
    heading("3. A binomial model for counts")
    body(f"Let Y = I(A), a Bernoulli variable with E[Y] = p = {m['Unweighted P(A), BP cohort']:.5f} "
         f"and Var(Y) = p(1-p) = {m['Bernoulli variance']:.4f}. For 20 independent uniform draws "
         f"with replacement, the count K is binomial with E[K] = {m['Binomial mean']:.3f} "
         f"and Var(K) = {m['Binomial variance']:.3f} cases squared.")
    figure("binomial.png", 425, 190, "Figure 1. Simulated counts and two model probability mass functions.")
    body(f"In 10,000 equal-size draws without replacement (seed 1405), the count mean was "
         f"{m['Subsample mean']:.3f} and its variance was {m['Subsample variance']:.3f}. "
         "The exact model for a finite cohort is hypergeometric. The binomial is close because "
         "20/5,824 is small. NHANES cluster sampling and heterogeneous subgroups can violate "
         "the independent, common-probability model for real survey counts.")

    story.append(PageBreak())
    heading("4. Shape of the SBP distribution")
    body(f"Under the empirical distribution, E[X] = {m['SBP mean']:.2f} mmHg, "
         f"Var(X) = {m['SBP variance']:.2f} mmHg squared and SD = {m['SBP SD']:.2f} mmHg. "
         f"The variance averages squared deviations over all {len(df):,} rows. The median "
         f"is {m['SBP median']:.2f} mmHg and skewness is {m['SBP skewness']:.2f}.")
    figure("normal.png", 430, 177, "Figure 2. Empirical density, fitted normal density, and normal Q-Q plot.")
    body(f"The histogram has a longer right tail and the upper Q-Q points rise above the "
         f"reference line. Tukey's 1.5-IQR fences are {m['Lower Tukey fence']:.2f} and "
         f"{m['Upper Tukey fence']:.2f} mmHg, with {int(m['Below lower fence'])} observations below "
         f"and {int(m['Above upper fence'])} above. All observations enter the analysis. The "
         f"fitted normal places {m['Normal P(A)']:.2%} above the threshold versus "
         f"{m['Unweighted P(A), BP cohort']:.2%} empirically. The normal approximation is "
         "less suitable for tail probabilities than for a rough description of the center.")
    heading("5. Sleep and SBP")
    figure("sleep_sbp.png", 425, 201, "Figure 3. Each point represents one adult with both measurements.")
    body(f"The empirical covariance of sleep hours and SBP is {m['Sleep-SBP covariance']:.3f} "
         f"hour × mmHg across {len(pairs):,} complete pairs. The sign is positive and the "
         "point cloud shows little visible linear structure. This is an unadjusted, "
         "observational association and leaves the project's adjusted question for later phases.")

    story.append(PageBreak())
    heading("Sources and reproduction")
    for name, url in [
        ("CDC/NCHS BPXO_L measurement documentation",
         "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/BPXO_L.htm"),
        ("CDC/NCHS NHANES weighting tutorial",
         "https://wwwn.cdc.gov/nchs/nhanes/tutorials/weighting.aspx"),
    ]:
        body(f'<link href="{url}" color="#163d61">{name}</link><br/>{url}')
    body("The Phase 1 analytical CSV and its preparation steps are documented in data/README.md. "
         "Run python3 src/phase2.py to regenerate the CSV tables and figures and "
         "python3 src/build_phase2_report.py to rebuild this report.")

    def footer(canvas, doc):
        canvas.setFillColor(colors.HexColor("#496477"))
        canvas.setFont("Helvetica", 9)
        canvas.drawString(52, 36, "NHANES 2021-2023  /  Phase 2")
        canvas.drawRightString(A4[0] - 52, 36, str(doc.page))

    SimpleDocTemplate(str(ROOT / "reports/phase2.pdf"), pagesize=A4,
                      topMargin=46, bottomMargin=52, leftMargin=52, rightMargin=52,
                      title="Phase 2 | Probability and Distributions").build(
                          story, onFirstPage=footer, onLaterPages=footer)


if __name__ == "__main__":
    build()
