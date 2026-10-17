# NorthGrid Files: Loss Investigation Unit (v3, final)

Everything for the DataThon NASCON'26 submission: data cleaning, every answer (A1 to C6), the tampering model
(`predictions_TEAMxx.csv`), a one-screen dashboard and an auto-generated answer document.

## What's in the box

| Path | What it does |
|---|---|
| `run_all.py` | Runs steps 1 to 6 in order |
| `ng/s01_load.py` | Finds every extract file, loads it into DuckDB, cleans it and writes the data-quality log (**A2**) |
| `ng/s02_losses.py` | **A1** consumer count, **A3** real vs IT loss with a fix-by-fix bridge, **B1**, billing gap (**C1/C2**), **B4**, **C3** |
| `ng/s03_loadshed.py` | **B3** load-shedding vs losses (which drives which) |
| `ng/s04_theft_model.py` | **P2** tampering model + submission CSV, **C4** transformers and total tampered meters |
| `ng/s05_insider.py` | **C5** meter-reader profiling (MRDN route) |
| `ng/s06_answers.py` | **C6** pp breakdown, **B2** director verdicts, writes `outputs/ANSWERS.md` |
| `ng/s07_detective.py` | **Loss Detective**: finds each sub-division's break month and puts every suspect on trial (billing software, bill-vs-meter gap, weather, load-shedding, tampering wave, reader route, data artefacts), in pp explained |
| `ng/s08_network.py` | **Transformer Crime Network**: links suspicious meters through transformer, reader and same-month drops into rings |
| `dashboard.py` | 8-page interactive Loss Command Center: Control Room, Loss Detective, Crime Network, Meter X-Ray (explainable AI), Sub-divisions, Recovery Simulator, Data Trust, Board Pitch. Global sub-division filter and click-through drill-downs |
| `outputs/` | Results from the provisional run on 3 sub-divisions (see "Status of the bundled outputs") |

## Step by step in VS Code

**1. Install the tools (once)**
- Python 3.10 or newer from python.org. On Windows, tick **"Add python.exe to PATH"** during install.
- VS Code, then the **Python** extension (Extensions panel, search "Python", publisher Microsoft).

**2. Open the project**
- Unzip `northgrid_v3.zip` somewhere with at least **15 GB free** (DuckDB needs scratch space).
- VS Code: **File > Open Folder…** and pick the `northgrid_v3` folder.

**3. Put the data in place**
- Create a folder named `data` inside `northgrid_v3`.
- Copy the whole `PWRDIST_ENT_DWH_EXTRACT_FY2324_FY2526_FULLREFRESH` folder into `data/`. Sub-folders are fine:
  the code searches every level for files by name, so you don't need to flatten them.
- Or leave the data where it is and pass `--data "D:\path\to\PWRDIST_ENT_..."` in step 5.

**4. Create the environment** (Terminal > New Terminal)
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate
pip install -r requirements.txt
```
If VS Code asks "select interpreter", choose the one inside `.venv`.

**5. Run everything** (for the GPU: `pip install xgboost` is already in requirements)
```bash
python run_all.py --team TEAM07
```
Replace `TEAM07` with your team number (or write it once in a file named `team.txt` next to `run_all.py`).
Without a team name the file is called `predictions_TEAMxx.csv` and the run prints a warning. On a laptop with 16 GB RAM the full 11 GB extract takes roughly 15 to 30
minutes; step 1 (loading) is the slow part. On 8 GB RAM add `--mem 4GB`.

If a step fails, fix it and resume without reloading: `python run_all.py --from 2` (or 3..8).
You can also run one step alone: `python -m ng.s04_theft_model`.

**6. Read the results**
- `outputs/ANSWERS.md`: the answer document, labelled A1 to C6. Right-click > **Open Preview** in VS Code.
  Paste it into Word/Google Docs for submission, reviewing the B2 verdicts and the C5 suspect yourself.
- `outputs/predictions_TEAM07.csv`: the P2 submission (exactly `MTR_SRL_NO,THEFT_SCORE`, one row per test meter).
- `outputs/dq_log.csv`: the A2 data-quality log.

**7. Dashboard**
```bash
streamlit run dashboard.py
```
It opens in the browser. Take screenshots for the submission, or present it live.

**8. Zip for submission**: answer document, `predictions_TEAMxx.csv`, dashboard screenshots, and this whole folder
(code) without `data/` and `work/`.

## What's new in v3

- **Answer document reads like a report**: every answer is prose plus proper tables (consumers by sub-division,
  CV results, billing go-live dates, cost by sub-division, the C5 reader evidence, B2 tariff ratios). No raw Python
  output, no `nan`: sub-divisions without a break say "no sustained break", and those still on v5.1 say
  "no upgrade (still v5.1)".
- **Plain-English evidence** for every meter signal (no more `pk l6 = 0.378`).
- **Interactive dashboard**: one sub-division filter in the sidebar drives every page; click a sub-division bar to
  open its Loss Detective case, click a meter on the crime map to open it in Meter X-Ray, select table rows to drill
  into rings, meters and cases. Responsive layout, wrapped labels, no overlapping text, no emojis.
- Needs `streamlit>=1.40` (in requirements).

## What was new in v2

- **4-5x faster loading**: AMI files are typed, de-duplicated and rolled up one file at a time (9 files in ~2 min here).
- **GPU model**: XGBoost on your NVIDIA GPU (`device=cuda`), detected automatically, otherwise it falls back to CPU.
  Bagged boosting (3 seeds) blended with extra-trees; CV picks the best feature set/blend on Precision@500.
  For GPU: `pip install xgboost` (the pip wheel includes CUDA on Windows/Linux) and an NVIDIA driver.
- **New features**: neighbour-relative collapse, peak/off-peak shift, offline days, billed-vs-metered ratio and more.
- **Explainable AI**: every top meter gets its 3 strongest reasons in plain words with the typical value beside
  them (ablation attribution). See `outputs/meter_evidence.csv` and the Meter X-Ray page.
- **Loss Detective**, **Crime Network**, **Recovery Simulator** (PKR from re-billing, raids, fixing the software),
  **3-minute pitch script** (`outputs/PITCH.md`).

## Traps the code handles (A2 highlights)

- FY2025-26 AMI files rename `KWH_OFFPEAK` to `KWH_OFF_PK` (schema drift).
- MRDN SCADA file is stamped in UTC while the README says PKT: shifted +5h (detected per file automatically).
- About 115 SCADA hours logged in Wh (1000x the hour's peak demand): divided by 1000.
- SCADA duplicate feeder-hours, missing hours (imputed by feeder, month and hour).
- Bills: superseded revisions (keep the latest), `BILL_MNTH` in two formats (`2024-09` and `Sep-24`).
- AMI: about 48k exact duplicate rows, sentinel 999999, negative kWh, missing flags.
- Consumer master is SCD2: A1 uses the row valid on 30-Jun-2026, not `CURR_FLG`.
- Labels: features cut at each meter's inspection date (no leakage); CV grouped by transformer (selection bias).

## Status of the bundled outputs (read before submitting)

The included `outputs/` (and the dashboard you see) come from a run on the files uploaded so far: **meter readings, billing and SCADA for
MRDN (ZN11), CHKW (ZN13) and JHLM (ZN14) only**. These were missing: the consumer master, asset register and outage
log for all zones, every file for ZN02, ZN03, ZN05, ZN07 and ZN08, the vigilance labels and the test meter list.
As a result:
- **A1, B2 (Ops, Commercial), B3 feeder-level, C4, crime-network transformer/reader links and C5 billed-vs-metered** show "n/a"/"pending" or use fallbacks.
- **P2**: no `predictions_*.csv` until `SUBMSN_TEMPLATE_TEST_MTR_LIST.csv` is present; without labels the model
  falls back to an unsupervised score.
- All company-wide numbers cover 3 of 8 sub-divisions.

Re-running `python run_all.py --team TEAM07` on the full extract fills all of this in automatically.

## Headline finding so far (3 sub-divisions)

Units billed matched smart-meter kWh (ratio ≈ 1.00) until the billing system moved from v5.1 to v5.2 (MRDN Mar-2025,
CHKW Jun-2025). From that month the ratio falls to about 0.87 to 0.93. JHLM, still on v5.1, stays at 1.00. Losses
rose about 9 to 10pp in MRDN and CHKW, against under 2pp in JHLM. Bills are raised from meter readers' readings,
not AMI (README), so check readers as well as software (C5).
