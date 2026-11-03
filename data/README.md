# Data

Raw data files are **not** committed to this repository (per course rules,
Section 11). This file documents the official source, retrieval process, and
how to reproduce `data/raw/` locally.

## Official source

National Health and Nutrition Examination Survey (NHANES), U.S. CDC/NCHS —
public-use data, cycle **August 2021 &ndash; August 2023** (file suffix `_L`).

- Cycle landing page: https://wwwn.cdc.gov/nchs/nhanes/continuousnhanes/default.aspx?BeginYear=2021
- Data files index: https://wwwn.cdc.gov/nchs/nhanes/search/datapage.aspx?Component=Examination&Cycle=2021-2023

## Files used in this project

| File | Component | Download URL |
|---|---|---|
| DEMO_L | Demographics & sample weights | `https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/DEMO_L.xpt` |
| BPXO_L | Blood pressure (oscillometric) | `https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/BPXO_L.xpt` |
| BMX_L | Body measures | `https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/BMX_L.xpt` |
| SLQ_L | Sleep disorders questionnaire | `https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/SLQ_L.xpt` |
| PAQ_L | Physical activity questionnaire | `https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/PAQ_L.xpt` |
| SMQ_L | Smoking - cigarette use questionnaire | `https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/SMQ_L.xpt` |

Retrieved: 2026-11-03 (1405-08-12). No access application was required; all
files are public-use.

## How to reproduce locally

```bash
mkdir -p data/raw
BASE="https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles"
for f in DEMO_L BPXO_L BMX_L SLQ_L PAQ_L SMQ_L; do
  curl -sS -o "data/raw/${f}.xpt" "${BASE}/${f}.xpt"
done
```

Then run `python3 src/analysis.py`'s `merge_and_clean()` (see
`notebooks/phase1_exploration.ipynb`), which merges the six files on `SEQN`,
applies the Phase 1 analytic-population filters, and writes a small cleaned
CSV to `data/processed/phase1_analytic.csv` (this processed file *is*
committed — it is small, ~5.8k rows, and contains no raw/bulk government
data, only the derived analytic columns).

## Record of resampling / re-cleaning

| Date | Change |
|---|---|
| 2026-11-03 | Initial download of the six 2021-2023 component files; Phase 1 merge, cleaning and analytic-population definition. |

## Merge and filtering summary (Phase 1)

- Base file `DEMO_L`: 11,933 rows (one per NHANES participant).
- All six files merge 1:1 on `SEQN` with no duplicates.
- Analytic population filters applied, in order:
  1. Excluded not fully MEC-examined (`RIDSTATR != 2`): 3,073
  2. Excluded age < 20: 2,796
  3. Excluded pregnant at exam (`RIDEXPRG == 1`): 41
  4. Excluded no valid systolic BP reading: 199
- **Final analytic sample: 5,824 adults.**

See `reports/phase1.pdf` (Section A4) for the full inclusion/exclusion
rationale.
