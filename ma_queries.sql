-- ─────────────────────────────────────────────────────────────────────────────
--  M&A DEAL TRACKER — SQL Analytics Suite
--  Author  : Praveen Kumar Nutakki
--  Purpose : Pipeline intelligence, stage velocity, fee analysis,
--            valuation benchmarking and anomaly detection
--  Database: MeridianCFO  (add new tables to existing DB)
-- ─────────────────────────────────────────────────────────────────────────────

USE MeridianCFO;
GO

-- ─────────────────────────────────────────────────────────────────────────────
-- QUERY 1: Pipeline Summary by Stage and Sector
-- Business Need: Show the CFO and deal team exactly where every deal
--               sits, how much value is in each stage, and which
--               sectors are driving the most pipeline activity
-- ─────────────────────────────────────────────────────────────────────────────

SELECT
    ds.stage_name,
    ds.stage_order,
    sec.sector_name,

    COUNT(DISTINCT fa.deal_id)              AS deal_count,

    ROUND(SUM(fa.deal_value_usd_m), 1)      AS total_value_usd_m,

    ROUND(AVG(fa.deal_value_usd_m), 1)      AS avg_deal_value_usd_m,

    ROUND(SUM(fa.advisory_fee_usd_m), 2)    AS total_fees_usd_m,

    CASE
        WHEN ds.stage_order >= 4 THEN 'HIGH'
        WHEN ds.stage_order = 3  THEN 'MEDIUM'
        ELSE 'PIPELINE'
    END AS pipeline_priority

FROM fact_deal_activity   fa
JOIN dim_stage            ds  ON fa.stage_id   = ds.stage_id
JOIN dim_sector           sec ON fa.sector_id  = sec.sector_id
WHERE fa.is_current_stage = 1
GROUP BY
    ds.stage_name, ds.stage_order,
    sec.sector_name
ORDER BY
    ds.stage_order,
    total_value_usd_m DESC;
GO


-- ─────────────────────────────────────────────────────────────────────────────
-- QUERY 2: Stage Velocity Analysis — Avg Days per Stage with Stall Detection
-- Business Need: Identify which deals are taking abnormally long in
--               each stage so the deal team can intervene before
--               a transaction loses momentum or the client disengages
-- Anomaly Caught: DEAL-003, DEAL-009, DEAL-019 stalled in Due Diligence
-- ─────────────────────────────────────────────────────────────────────────────

WITH stage_times AS (
    SELECT
        fa.deal_id,
        dd.deal_type,
        sec.sector_name,
        ds.stage_name,
        ds.stage_order,
        ds.typical_days                     AS benchmark_days,
        fa.days_in_stage                    AS actual_days,
        fa.status_note,

        ROUND(
            CAST(fa.days_in_stage AS FLOAT) /
            NULLIF(ds.typical_days, 0) * 100
        , 1)                                AS pct_of_benchmark

    FROM fact_deal_activity   fa
    JOIN dim_stage            ds  ON fa.stage_id  = ds.stage_id
    JOIN dim_deal             dd  ON fa.deal_id   = dd.deal_id
    JOIN dim_sector           sec ON fa.sector_id = sec.sector_id
)

SELECT
    deal_id,
    sector_name,
    stage_name,
    benchmark_days,
    actual_days,
    pct_of_benchmark,
    status_note,

    CASE
        WHEN pct_of_benchmark > 250 THEN 'CRITICAL STALL'
        WHEN pct_of_benchmark > 175 THEN 'WARNING'
        WHEN pct_of_benchmark > 130 THEN 'SLOW'
        ELSE 'ON TRACK'
    END AS velocity_flag,

    CASE
        WHEN pct_of_benchmark > 175
        THEN 'Escalate to senior advisor — risk of deal fatigue'
        WHEN pct_of_benchmark > 130
        THEN 'Schedule check-in with client within 5 business days'
        ELSE 'No action required'
    END AS recommended_action

FROM stage_times
ORDER BY
    pct_of_benchmark DESC,
    deal_id;
GO


-- ─────────────────────────────────────────────────────────────────────────────
-- QUERY 3: Advisory Fee Ratio Analysis by Sector
-- Business Need: Benchmark advisory fees as % of deal value across
--               sectors to ensure pricing consistency and flag outliers
--               that may indicate scope creep or billing errors
-- Anomaly Caught: DEAL-014 fee ratio at 7.1% vs 1.5–3% sector norm
-- ─────────────────────────────────────────────────────────────────────────────

WITH fee_ratios AS (
    SELECT
        dd.deal_id,
        dd.target_name,
        sec.sector_name,
        dd.deal_value_usd_m,
        dd.advisory_fee_usd_m,

        ROUND(
            dd.advisory_fee_usd_m /
            NULLIF(dd.deal_value_usd_m, 0) * 100
        , 2)                                AS fee_pct_of_deal

    FROM dim_deal    dd
    JOIN dim_sector  sec ON dd.sector_id = sec.sector_id
),

sector_benchmarks AS (
    SELECT
        sector_name,
        AVG(fee_pct_of_deal)    AS avg_fee_pct,
        STDEV(fee_pct_of_deal)  AS std_fee_pct
    FROM fee_ratios
    GROUP BY sector_name
)

SELECT
    fr.deal_id,
    fr.target_name,
    fr.sector_name,
    fr.deal_value_usd_m,
    fr.advisory_fee_usd_m,
    fr.fee_pct_of_deal,

    ROUND(sb.avg_fee_pct, 2)    AS sector_avg_fee_pct,
    ROUND(sb.std_fee_pct, 2)    AS sector_std_fee_pct,

    ROUND(
        ABS(fr.fee_pct_of_deal - sb.avg_fee_pct) /
        NULLIF(sb.std_fee_pct, 0)
    , 2)                        AS std_deviations_from_mean,

    CASE
        WHEN ABS(fr.fee_pct_of_deal - sb.avg_fee_pct) >
             2 * NULLIF(sb.std_fee_pct, 0)
        THEN 'FEE ANOMALY — REVIEW REQUIRED'
        ELSE 'WITHIN NORMAL RANGE'
    END AS fee_flag

FROM fee_ratios          fr
JOIN sector_benchmarks   sb ON fr.sector_name = sb.sector_name
ORDER BY
    fr.fee_pct_of_deal DESC;
GO


-- ─────────────────────────────────────────────────────────────────────────────
-- QUERY 4: EV/EBITDA Valuation Benchmarking
-- Business Need: Compare each deal's valuation multiple against the
--               sector benchmark to identify overvalued targets,
--               pricing anomalies, and negotiation opportunities
-- Anomaly Caught: DEAL-007 EV/EBITDA at 31.4x vs 14.5x sector norm
-- ─────────────────────────────────────────────────────────────────────────────

SELECT
    dd.deal_id,
    dd.target_name,
    dd.deal_type,
    dd.geography,
    sec.sector_name,
    sec.ev_ebitda_benchmark             AS sector_ev_ebitda_benchmark,
    dd.ev_ebitda_multiple               AS deal_ev_ebitda_multiple,
    dd.deal_value_usd_m,
    dd.ebitda_usd_m,

    ROUND(
        dd.ev_ebitda_multiple -
        sec.ev_ebitda_benchmark
    , 1)                                AS premium_to_benchmark,

    ROUND(
        (dd.ev_ebitda_multiple -
         sec.ev_ebitda_benchmark) /
        NULLIF(sec.ev_ebitda_benchmark, 0) * 100
    , 1)                                AS premium_pct,

    CASE
        WHEN dd.ev_ebitda_multiple >
             sec.ev_ebitda_benchmark * 1.40
        THEN 'OVERVALUED — FLAG FOR REVIEW'
        WHEN dd.ev_ebitda_multiple >
             sec.ev_ebitda_benchmark * 1.15
        THEN 'ABOVE BENCHMARK'
        WHEN dd.ev_ebitda_multiple <
             sec.ev_ebitda_benchmark * 0.85
        THEN 'BELOW BENCHMARK — POTENTIAL OPPORTUNITY'
        ELSE 'FAIRLY VALUED'
    END AS valuation_flag,

    dst.stage_name                      AS current_stage

FROM dim_deal    dd
JOIN dim_sector  sec ON dd.sector_id       = sec.sector_id
JOIN dim_stage   dst ON dd.current_stage_id = dst.stage_id
ORDER BY
    premium_pct DESC;
GO
