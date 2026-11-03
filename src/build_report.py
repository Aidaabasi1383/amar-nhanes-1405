"""Builds reports/phase1.pdf from the same analysis pipeline used by the
notebook, so the two deliverables never diverge. Run after the notebook has
been executed (figures must already exist in figures/).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analysis as A

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image,
    PageBreak, ListFlowable, ListItem, KeepTogether,
)

ROOT = Path(__file__).resolve().parents[1]
FIG_DIR = ROOT / "figures"
OUT_PATH = ROOT / "reports" / "phase1.pdf"

styles = getSampleStyleSheet()
styles.add(ParagraphStyle("H1c", parent=styles["Heading1"], spaceBefore=14, spaceAfter=8))
styles.add(ParagraphStyle("H2c", parent=styles["Heading2"], spaceBefore=10, spaceAfter=6))
styles.add(ParagraphStyle("Body", parent=styles["BodyText"], spaceAfter=8, leading=14))
styles.add(ParagraphStyle("Small", parent=styles["BodyText"], fontSize=8.5, textColor=colors.grey))
styles.add(ParagraphStyle("Quote", parent=styles["BodyText"], leftIndent=18, textColor=colors.HexColor("#1b3a5c"),
                           borderPadding=6, backColor=colors.HexColor("#eef3f8")))


def df_to_table(df, col_widths=None, font_size=8.5):
    data = [list(df.columns)] + df.astype(str).values.tolist()
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), font_size),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f6f8")]),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def build():
    analytic, counts = A.merge_and_clean()

    story = []

    # ---------------- title page ----------------
    story.append(Spacer(1, 3 * cm))
    story.append(Paragraph("Statistics &amp; Applications Project &ndash; Fall 1405", styles["Title"]))
    story.append(Paragraph("Phase 1: Study Design, Data, and Descriptive Statistics", styles["Heading2"]))
    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph("Track A &ndash; NHANES 2021&ndash;2023", styles["Heading3"]))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph("Student: Aida Abasi &ndash; Student ID: 401170897", styles["Heading3"]))
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph(
        "Working research question: Is mean systolic blood pressure among U.S. adults "
        "(20+) associated with usual sleep duration, sedentary time, smoking status, "
        "and BMI, after accounting for age and sex?", styles["Quote"]))
    story.append(Spacer(1, 2 * cm))
    story.append(Paragraph(
        "This report, the companion notebook (notebooks/phase1_exploration.ipynb), "
        "and the reusable pipeline (src/analysis.py) were produced together so that all "
        "numbers below are reproducible end-to-end from the raw CDC files listed in "
        "data/README.md.", styles["Small"]))
    story.append(PageBreak())

    # ---------------- 1. source & collection ----------------
    story.append(Paragraph("1. Data Source and Collection Mechanism", styles["H1c"]))
    story.append(Paragraph(
        "Official source: the National Health and Nutrition Examination Survey "
        "(NHANES), conducted by the U.S. National Center for Health Statistics (NCHS), "
        "part of the CDC. This project uses the August 2021&ndash;August 2023 cycle "
        "(file suffix <i>_L</i>), a combined, non-standard cycle released to bridge the "
        "data collection gap caused by the COVID-19 pandemic (data collection was "
        "suspended for part of 2020). Because of this, the cycle's sample weights "
        "(WTMEC2YR, WTINT2YR) are already scaled for this single two-year release and "
        "require no further adjustment.", styles["Body"]))
    story.append(Paragraph(
        "Collection mechanism: a two-stage design &mdash; (1) an in-home interview "
        "covering demographics and lifestyle questionnaires (sleep, physical activity, "
        "smoking), and (2) a physical examination at a Mobile Examination Center (MEC), "
        "where trained staff measure body size and blood pressure with an oscillometric "
        "device. All files used are public-use and required no special access "
        "application.", styles["Body"]))

    files_tbl = [["File", "Component"],
                 ["DEMO_L", "Demographics & sample weights (base file)"],
                 ["BPXO_L", "Blood pressure - oscillometric measurements"],
                 ["BMX_L", "Body measures (height, weight, BMI, waist)"],
                 ["SLQ_L", "Sleep disorders questionnaire"],
                 ["PAQ_L", "Physical activity questionnaire"],
                 ["SMQ_L", "Smoking - cigarette use questionnaire"]]
    story.append(Table(files_tbl, colWidths=[3 * cm, 11 * cm], style=TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f6f8")]),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ])))
    story.append(Spacer(1, 10))

    # ---------------- 2. observation unit ----------------
    story.append(Paragraph("2. Observation Unit and Data Structure", styles["H1c"]))
    story.append(Paragraph(
        "Each row represents one survey respondent, uniquely identified by SEQN across "
        "every component file. The data are stored wide (one row per person); the six "
        "component files were merged on SEQN. There is no repeated-visit hierarchy in "
        "this subset; the only within-row repetition is three consecutive blood-pressure "
        "readings (BPXOSY1&ndash;3), averaged into the main response variable.", styles["Body"]))

    # ---------------- 3. sampling & generalizability ----------------
    story.append(Paragraph("3. Sampling, Selection, and Generalizability", styles["H1c"]))
    story.append(Paragraph(
        "NHANES uses a complex multistage, stratified, clustered probability design with "
        "deliberate oversampling of specific subgroups (e.g., older adults, certain "
        "race/ethnicity groups, lower-income persons) to improve precision for those "
        "subgroups. This is an observational cross-sectional study (random sampling from "
        "a population, not random assignment to treatment). Consequently, respondents do "
        "not represent the population equally; the MEC sample weight corrects for this "
        "(Section A2/A3). Weighted results generalize to the U.S. civilian "
        "noninstitutionalized population aged 20+ during 2021&ndash;2023, not to "
        "institutionalized populations or to other countries.", styles["Body"]))

    # ---------------- 4. variable classification ----------------
    story.append(Paragraph("4. Classification of Key Variables", styles["H1c"]))
    var_tbl = [
        ["Variable", "Description", "Type", "Scale"],
        ["sbp_mean", "Mean systolic BP (3 readings)", "Quantitative, continuous", "Ratio"],
        ["bmi", "Body mass index", "Quantitative, continuous", "Ratio"],
        ["sleep_hours", "Usual weekday sleep duration", "Quantitative, continuous", "Ratio"],
        ["sedentary_min", "Daily sedentary minutes", "Quantitative, continuous", "Ratio"],
        ["age_years", "Age in years", "Quantitative, discrete", "Ratio"],
        ["age_group", "Age group (20-39/40-59/60+)", "Qualitative", "Ordinal"],
        ["sex", "Sex", "Qualitative", "Nominal (binary)"],
        ["education", "Education level", "Qualitative", "Ordinal"],
        ["smoking_status", "Smoking status (4 levels)", "Qualitative", "Nominal"],
    ]
    story.append(df_to_table(__import__("pandas").DataFrame(var_tbl[1:], columns=var_tbl[0]),
                              col_widths=[2.6 * cm, 6.2 * cm, 3.3 * cm, 2.6 * cm]))
    story.append(PageBreak())

    # ---------------- 5. data quality ----------------
    story.append(Paragraph("5. Data Quality Audit", styles["H1c"]))
    story.append(Paragraph(
        "NHANES refused/don't-know sentinel codes (e.g., 7, 9, 7777, 9999 depending on "
        "the variable) in PAD680, SMQ040, SMQ020 and DMDEDUC2 were recoded to missing "
        "before analysis, since they are not valid numeric responses and would otherwise "
        "severely distort means (e.g., a sentinel of 7777 minutes of sedentary time). "
        "No rows were dropped at this stage &mdash; missing values are simply ignored "
        "locally in each computation.", styles["Body"]))
    cols = ["sbp_mean", "bmi", "sleep_hours", "sedentary_min", "age_years", "sex",
            "education", "smoking_status"]
    dq = A.data_quality_report(analytic, cols)
    story.append(df_to_table(dq, col_widths=[4 * cm, 3 * cm, 3 * cm, 3 * cm]))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "Plausibility check: no systolic BP values outside 70&ndash;250 mmHg, no BMI "
        "outside 10&ndash;80, and no sleep duration outside 2&ndash;16 hours were found "
        "in the analytic sample, so no observations were removed as implausible outliers "
        "in Phase 1.", styles["Body"]))

    # ---------------- 6. frequency tables ----------------
    story.append(Paragraph("6. Frequency Tables (Categorical Variables)", styles["H1c"]))
    import pandas as pd
    for c in ["sex", "age_group", "smoking_status"]:
        vc = analytic[c].astype("object").fillna("Missing").value_counts()
        pct = (100 * vc / len(analytic)).round(1)
        t = pd.DataFrame({c: vc.index.astype(str), "freq": vc.values, "pct": pct.values})
        story.append(Paragraph(f"<b>{c}</b>", styles["H2c"]))
        story.append(df_to_table(t, col_widths=[6 * cm, 3 * cm, 3 * cm]))
        story.append(Spacer(1, 6))

    story.append(PageBreak())

    # ---------------- 7. center & spread ----------------
    story.append(Paragraph("7. Center and Spread of Key Quantitative Variables", styles["H1c"]))
    cs = A.center_spread_table(analytic, ["sbp_mean", "bmi", "sleep_hours", "sedentary_min", "age_years"])
    story.append(df_to_table(cs, col_widths=[2.6 * cm] + [1.8 * cm] * 7))

    # ---------------- 8. figures ----------------
    story.append(Paragraph("8. Visualizations", styles["H1c"]))
    fig_captions = [
        ("fig1_hist_sbp.png", "Figure 1. Distribution of mean systolic blood pressure."),
        ("fig2_box_sbp_smoking.png", "Figure 2. Systolic BP by current smoking status."),
        ("fig3_scatter_sleep_sbp.png", "Figure 3. Sleep duration vs. systolic BP (random subsample)."),
        ("fig4_bar_age_sex.png", "Figure 4. Analytic sample size by age group and sex."),
    ]
    for fname, cap in fig_captions:
        story.append(Image(str(FIG_DIR / fname), width=13 * cm, height=13 * cm * 4 / 6))
        story.append(Paragraph(cap, styles["Small"]))
        story.append(Spacer(1, 8))
    story.append(PageBreak())

    # ---------------- 9. descriptive comparisons ----------------
    story.append(Paragraph("9. Initial Descriptive Comparisons (No Inference Yet)", styles["H1c"]))
    story.append(Paragraph(
        "Only descriptive summaries are compared across groups here; no hypothesis test "
        "or p-value is reported in Phase 1 (that is the task of Phase 3).", styles["Body"]))
    for label, col in [("Systolic BP by smoking group", "smoker_group"),
                        ("Systolic BP by sex", "sex"),
                        ("Systolic BP by age group", "age_group")]:
        story.append(Paragraph(f"<b>{label}</b>", styles["H2c"]))
        g = A.group_compare_descriptive(analytic, "sbp_mean", col)
        story.append(df_to_table(g, col_widths=[4 * cm, 2.5 * cm, 2.5 * cm, 2.5 * cm, 2.5 * cm]))
        story.append(Spacer(1, 6))

    story.append(PageBreak())

    # ---------------- A1-A4 NHANES-specific ----------------
    story.append(Paragraph("Track-A (NHANES) Specific Requirements", styles["H1c"]))

    story.append(Paragraph("A1. File Identification and Merge Key", styles["H2c"]))
    story.append(Paragraph(
        "The common merge key across all NHANES files is SEQN. DEMO_L was used as the "
        "base file because every participant has a DEMO_L row; the other five files "
        "were left-joined on SEQN so no base participant is dropped due to missing data "
        "in a sub-component (real exclusions only happen later, in A4, under an explicit "
        "rule). No duplicate SEQN values were found in any file.", styles["Body"]))

    story.append(Paragraph("A2. Identifying the Appropriate Weight and Sampling Design", styles["H2c"]))
    story.append(Paragraph(
        "Because the main response (sbp_mean) and the body-measure variables come from "
        "the MEC physical exam (not just the interview), the correct weight is "
        "<b>WTMEC2YR</b>, not WTINT2YR (which is only valid for interview-only analyses). "
        "Using the wrong weight, or ignoring weights entirely, biases population estimates "
        "because oversampled respondents represent a different number of population "
        "members. The design variables SDMVSTRA (stratum) and SDMVPSU (primary sampling "
        f"unit) were also identified for correct variance estimation in Phase 3 "
        f"({analytic['SDMVSTRA'].nunique()} strata, {analytic['SDMVPSU'].nunique()} PSUs "
        "observed in this subset).", styles["Body"]))

    story.append(Paragraph("A3. Raw vs. Weighted Summary Comparison", styles["H2c"]))
    story.append(df_to_table(A.weighted_vs_unweighted(analytic),
                              col_widths=[3.5 * cm, 3.5 * cm, 3.5 * cm, 3.5 * cm]))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "The unweighted mean treats every respondent equally; the weighted mean weighs "
        "each respondent by how many population members they represent "
        "(&sum;w<sub>i</sub>x<sub>i</sub> / &sum;w<sub>i</sub>). The gap between the two "
        "reflects the effect of the complex (oversampled) design, not a data error.",
        styles["Body"]))

    story.append(Paragraph("A4. Defining the Analytic Population", styles["H2c"]))
    incl = [
        "Adults aged 20 and older (RIDAGEYR &ge; 20)",
        "Both interviewed and MEC-examined (RIDSTATR == 2), since blood pressure and BMI require the exam",
        "At least one valid systolic BP reading",
    ]
    story.append(Paragraph("Inclusion criteria:", styles["Body"]))
    story.append(ListFlowable([ListItem(Paragraph(i, styles["Body"])) for i in incl], bulletType="bullet"))
    story.append(Paragraph(
        "Exclusion criterion: participants who were pregnant at exam time (RIDEXPRG == 1) "
        "were excluded, since pregnancy materially alters blood pressure and metabolic "
        "physiology and could confound the relationship under study.", styles["Body"]))

    flow_tbl = [
        ["Step", "N"],
        ["Merged total (before filters)", str(counts["n_before_filters"])],
        ["Excluded: not fully MEC-examined", str(counts["excluded_not_mec_examined"])],
        ["Excluded: age under 20", str(counts["excluded_under_20"])],
        ["Excluded: pregnant", str(counts["excluded_pregnant"])],
        ["Excluded: no valid BP reading", str(counts["excluded_no_valid_bp"])],
        ["Final analytic sample", str(counts["n_analytic_sample"])],
    ]
    story.append(Spacer(1, 8))
    story.append(KeepTogether(Table(flow_tbl, colWidths=[9 * cm, 4 * cm], style=TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("ALIGN", (1, 0), (1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))))

    story.append(PageBreak())

    # ---------------- 10. finalized question ----------------
    story.append(Paragraph("10. Finalized Statistical Question", styles["H1c"]))
    story.append(Paragraph(
        f"Given the analytic sample (N = {counts['n_analytic_sample']} adults), good "
        "data quality (under 1% missing on most key variables), and an observable "
        "descriptive gap between smoking groups, the project's main statistical question "
        "is finalized as:", styles["Body"]))
    story.append(Paragraph(
        "Is mean systolic blood pressure among U.S. adults aged 20+ (NHANES "
        "2021&ndash;2023) associated with usual sleep duration, daily sedentary time, "
        "smoking status, and BMI, after controlling for age and sex?", styles["Quote"]))
    story.append(Paragraph(
        "This is a relational / predictive question (addressed with multiple regression "
        "in Phase 4), built up through Phase 2 (probability distributions) and Phase 3 "
        "(estimation and hypothesis testing). No definitive causal claim is made, since "
        "this is a cross-sectional observational study.", styles["Body"]))

    doc = SimpleDocTemplate(str(OUT_PATH), pagesize=A4,
                             topMargin=2 * cm, bottomMargin=2 * cm,
                             leftMargin=2 * cm, rightMargin=2 * cm,
                             title="Phase 1 Report - Statistics Project")
    doc.build(story)
    print("wrote", OUT_PATH)


if __name__ == "__main__":
    build()
