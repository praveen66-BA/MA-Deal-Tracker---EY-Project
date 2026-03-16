# ─────────────────────────────────────────────────────────────────────────────
#  M&A DEAL TRACKER — Synthetic Data Generator
#  Author : Praveen Kumar Nutakki
#  Purpose: Generate realistic M&A pipeline data for EY BI project
#  Output : data/raw/  (6 CSV files)
# ─────────────────────────────────────────────────────────────────────────────

import pandas as pd
import numpy as np
import random
import os

np.random.seed(99)
random.seed(99)

OUT = "data/raw/"
os.makedirs(OUT, exist_ok=True)

print("=" * 60)
print("  M&A DEAL TRACKER — DATA GENERATION")
print("=" * 60)

# ── 1. DIM_DATE ───────────────────────────────────────────────────────────────
dates = pd.date_range("2023-01-01", "2026-03-31", freq="D")
dim_date = pd.DataFrame({
    "date_id":       dates.strftime("%Y%m%d").astype(int),
    "full_date":     dates,
    "day":           dates.day,
    "month":         dates.month,
    "month_name":    dates.strftime("%B"),
    "quarter":       dates.quarter,
    "quarter_name":  "Q" + dates.quarter.astype(str),
    "year":          dates.year,
    "fiscal_period": dates.strftime("%Y-%m"),
    "is_month_end":  dates.is_month_end.astype(int),
    "is_quarter_end":dates.is_quarter_end.astype(int),
})
dim_date.to_csv(f"{OUT}dim_date.csv", index=False)
print(f"STEP 1/6 — dim_date            {len(dim_date):>6,} rows")

# ── 2. DIM_SECTOR ─────────────────────────────────────────────────────────────
dim_sector = pd.DataFrame({
    "sector_id":   [1, 2, 3, 4, 5],
    "sector_name": ["Technology & Software",
                    "Healthcare & Life Sciences",
                    "Financial Services",
                    "Industrial & Manufacturing",
                    "Consumer & Retail"],
    "ev_ebitda_benchmark": [22.5, 18.0, 14.5, 10.0, 12.0],
    "avg_deal_size_usd_m": [320, 280, 450, 180, 210],
    "ey_practice_area":    ["Transaction Advisory", "Life Sciences Advisory",
                            "Financial Services Advisory",
                            "Industrial Advisory", "Consumer Advisory"]
})
dim_sector.to_csv(f"{OUT}dim_sector.csv", index=False)
print(f"STEP 2/6 — dim_sector          {len(dim_sector):>6,} rows")

# ── 3. DIM_STAGE ──────────────────────────────────────────────────────────────
dim_stage = pd.DataFrame({
    "stage_id":        [1, 2, 3, 4, 5, 6],
    "stage_name":      ["Sourcing", "Initial Review", "Due Diligence",
                        "Negotiation", "Signing", "Closed"],
    "stage_order":     [1, 2, 3, 4, 5, 6],
    "typical_days":    [30, 21, 45, 30, 14, 7],
    "is_active_stage": [1, 1, 1, 1, 1, 0],
    "stage_type":      ["Pipeline", "Pipeline", "Active",
                        "Active", "Active", "Completed"]
})
dim_stage.to_csv(f"{OUT}dim_stage.csv", index=False)
print(f"STEP 3/6 — dim_stage           {len(dim_stage):>6,} rows")

# ── 4. DIM_DEAL ───────────────────────────────────────────────────────────────
targets = [
    ("AlphaWave Technologies",  1, "India"),
    ("Helix Pharma",            2, "India"),
    ("NovaBridge Capital",      3, "Singapore"),
    ("SteelPath Industries",    4, "India"),
    ("FreshMart Retail",        5, "India"),
    ("CloudSpark Inc",          1, "USA"),
    ("MedCore Diagnostics",     2, "UK"),
    ("Crestline Finance",       3, "India"),
    ("Precision Engineering",   4, "Germany"),
    ("Luxe Brands Group",       5, "UAE"),
    ("DataSentry Systems",      1, "India"),
    ("GenomeAxis Bio",          2, "India"),
    ("Atlas Leasing",           3, "India"),
    ("Ironforge Metals",        4, "India"),
    ("ZenithMart",              5, "India"),
    ("Quantum Analytics",       1, "Singapore"),
    ("CuraLife Health",         2, "USA"),
    ("PeakCredit Corp",         3, "India"),
    ("FoundryTech",             4, "India"),
    ("Orbit Consumer Goods",    5, "UK"),
    ("NexaCloud",               1, "India"),
    ("BioPath Sciences",        2, "India"),
    ("Sterling Investments",    3, "India"),
    ("HeavyLift Engineering",   4, "India"),
    ("BrandForce Retail",       5, "India"),
]

acquirers = [
    "EY Client — TechVentures Global", "EY Client — HealthEquity Partners",
    "EY Client — Apex Capital Group",  "EY Client — Titan Industries Ltd",
    "EY Client — Meridian Retail Corp","EY Client — TechVentures Global",
    "EY Client — HealthEquity Partners","EY Client — Apex Capital Group",
    "EY Client — Titan Industries Ltd", "EY Client — Meridian Retail Corp",
    "EY Client — NovaTech Fund",        "EY Client — HealthEquity Partners",
    "EY Client — Apex Capital Group",   "EY Client — Titan Industries Ltd",
    "EY Client — Meridian Retail Corp", "EY Client — NovaTech Fund",
    "EY Client — HealthEquity Partners","EY Client — Apex Capital Group",
    "EY Client — Titan Industries Ltd", "EY Client — Meridian Retail Corp",
    "EY Client — TechVentures Global",  "EY Client — HealthEquity Partners",
    "EY Client — Apex Capital Group",   "EY Client — Titan Industries Ltd",
    "EY Client — Meridian Retail Corp",
]

deal_types = ["Full Acquisition", "Majority Stake", "Minority Stake",
              "Merger", "Asset Purchase"]

rows = []
for i, (target, sector_id, geo) in enumerate(targets):
    base_val = dim_sector[dim_sector.sector_id == sector_id]["avg_deal_size_usd_m"].values[0]
    deal_val = round(base_val * np.random.uniform(0.6, 1.8), 1)
    ev_bench = dim_sector[dim_sector.sector_id == sector_id]["ev_ebitda_benchmark"].values[0]
    ebitda   = round(deal_val / (ev_bench * np.random.uniform(0.85, 1.20)), 1)
    ev_mult  = round(deal_val / ebitda, 1)

    # advisory fee: 1.5–3% of deal value
    fee_pct  = np.random.uniform(0.015, 0.030)
    adv_fee  = round(deal_val * fee_pct, 2)

    # current stage — spread across pipeline
    weights = [0.08, 0.12, 0.20, 0.20, 0.15, 0.25]
    current_stage = np.random.choice([1,2,3,4,5,6], p=weights)

    # deal start date — spread across 2023-2025
    start = pd.Timestamp("2023-01-01") + pd.Timedelta(days=random.randint(0, 900))
    start_id = int(start.strftime("%Y%m%d"))

    rows.append({
        "deal_id":           f"DEAL-{i+1:03d}",
        "target_name":       target,
        "acquirer_name":     acquirers[i],
        "sector_id":         sector_id,
        "geography":         geo,
        "deal_type":         random.choice(deal_types),
        "deal_value_usd_m":  deal_val,
        "ebitda_usd_m":      ebitda,
        "ev_ebitda_multiple": ev_mult,
        "advisory_fee_usd_m": adv_fee,
        "current_stage_id":  current_stage,
        "deal_start_date_id": start_id,
        "lead_advisor":      random.choice(["Rohan Mehta", "Ananya Singh",
                                            "Vikram Nair", "Priya Iyer",
                                            "Sanjay Pillai"]),
        "deal_status":       "Closed" if current_stage == 6 else
                             "Active" if current_stage >= 3 else "Pipeline"
    })

dim_deal = pd.DataFrame(rows)

# ── ANOMALY 1 — Deal-007 valuation spike (NovaBridge Capital) ────────────────
dim_deal.loc[dim_deal.deal_id == "DEAL-007", "ev_ebitda_multiple"] = 31.4
dim_deal.loc[dim_deal.deal_id == "DEAL-007", "deal_value_usd_m"]   = 820.0
print("  Anomaly 1 planted — DEAL-007 valuation spike (EV/EBITDA 31.4x)")

# ── ANOMALY 2 — Fee spike on DEAL-014 ────────────────────────────────────────
dim_deal.loc[dim_deal.deal_id == "DEAL-014", "advisory_fee_usd_m"] = \
    round(dim_deal.loc[dim_deal.deal_id == "DEAL-014", "deal_value_usd_m"].values[0] * 0.071, 2)
print("  Anomaly 2 planted — DEAL-014 advisory fee spike (7.1% of deal value)")

dim_deal.to_csv(f"{OUT}dim_deal.csv", index=False)
print(f"STEP 4/6 — dim_deal            {len(dim_deal):>6,} rows")

# ── 5. FACT_DEAL_ACTIVITY ─────────────────────────────────────────────────────
activity_rows = []

for _, deal in dim_deal.iterrows():
    start = pd.to_datetime(str(deal.deal_start_date_id), format="%Y%m%d")
    current_stg = int(deal.current_stage_id)
    cursor = start

    for stg in range(1, current_stg + 1):
        typical = dim_stage[dim_stage.stage_id == stg]["typical_days"].values[0]
        entry_date = cursor
        entry_id   = int(entry_date.strftime("%Y%m%d"))

        # ANOMALY 3 — stall deals in Due Diligence (DEAL-003, DEAL-009, DEAL-019)
        if deal.deal_id in ["DEAL-003","DEAL-009","DEAL-019"] and stg == 3:
            days_in = int(typical * np.random.uniform(2.8, 3.6))  # stalled
        else:
            days_in = int(typical * np.random.uniform(0.7, 1.5))

        exit_date = entry_date + pd.Timedelta(days=days_in)
        exit_id   = int(exit_date.strftime("%Y%m%d"))

        is_current = 1 if stg == current_stg else 0

        activity_rows.append({
            "activity_id":       f"ACT-{deal.deal_id}-S{stg}",
            "deal_id":           deal.deal_id,
            "stage_id":          stg,
            "entry_date_id":     entry_id,
            "exit_date_id":      exit_id if not is_current else None,
            "days_in_stage":     days_in,
            "is_current_stage":  is_current,
            "deal_value_usd_m":  deal.deal_value_usd_m,
            "advisory_fee_usd_m":deal.advisory_fee_usd_m,
            "sector_id":         deal.sector_id,
            "geography":         deal.geography,
            "status_note":       "STALLED" if (
                                    deal.deal_id in ["DEAL-003","DEAL-009","DEAL-019"]
                                    and stg == 3
                                 ) else "ON TRACK"
        })
        cursor = exit_date

fact_activity = pd.DataFrame(activity_rows)
fact_activity.to_csv(f"{OUT}fact_deal_activity.csv", index=False)
print(f"  Anomaly 3 planted — DEAL-003, DEAL-009, DEAL-019 stalled in Due Diligence")
print(f"STEP 5/6 — fact_deal_activity  {len(fact_activity):>6,} rows")

# ── 6. FACT_FEES_MONTHLY ──────────────────────────────────────────────────────
# Monthly fee accrual by deal for revenue tracking
fee_rows = []
for _, deal in dim_deal.iterrows():
    start = pd.to_datetime(str(deal.deal_start_date_id), format="%Y%m%d")
    months_active = int(deal.current_stage_id * 1.5) + 1
    monthly_fee = round(deal.advisory_fee_usd_m / max(months_active, 1), 3)
    for m in range(months_active):
        fee_date = start + pd.DateOffset(months=m)
        if fee_date > pd.Timestamp("2026-03-31"):
            break
        fee_rows.append({
            "fee_id":            f"FEE-{deal.deal_id}-M{m+1:02d}",
            "deal_id":           deal.deal_id,
            "sector_id":         deal.sector_id,
            "fiscal_period":     fee_date.strftime("%Y-%m"),
            "year":              fee_date.year,
            "month":             fee_date.month,
            "monthly_fee_usd_m": monthly_fee,
            "cumulative_pct":    round(min((m + 1) / months_active, 1.0) * 100, 1),
        })

fact_fees = pd.DataFrame(fee_rows)
fact_fees.to_csv(f"{OUT}fact_fees_monthly.csv", index=False)
print(f"STEP 6/6 — fact_fees_monthly   {len(fact_fees):>6,} rows")

# ── SUMMARY ───────────────────────────────────────────────────────────────────
total = sum([len(dim_date), len(dim_sector), len(dim_stage),
             len(dim_deal), len(fact_activity), len(fact_fees)])

print()
print("=" * 60)
print("  DATA GENERATION COMPLETE")
print("=" * 60)
print(f"  dim_date              {len(dim_date):>8,} rows")
print(f"  dim_sector            {len(dim_sector):>8,} rows")
print(f"  dim_stage             {len(dim_stage):>8,} rows")
print(f"  dim_deal              {len(dim_deal):>8,} rows")
print(f"  fact_deal_activity    {len(fact_activity):>8,} rows")
print(f"  fact_fees_monthly     {len(fact_fees):>8,} rows")
print("=" * 60)
print(f"  TOTAL                 {total:>8,} rows")
print("=" * 60)
print("  ANOMALIES PLANTED:")
print("  1  DEAL-007  EV/EBITDA valuation spike     31.4x")
print("  2  DEAL-014  Advisory fee spike             7.1% of deal")
print("  3  DEAL-003, 009, 019  Stalled Due Diligence  3x typical days")
print("=" * 60)
print("  All CSVs saved to data/raw/")
