"""
Statistics Engine for Earth Data Lab.
Performs deterministic, mathematically rigorous statistical calculations
using Pandas and NumPy without relying on external API keys or opaque models.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple


def calculate_summary_statistics(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Computes key descriptive statistics for temperature anomalies.
    """
    if df is None or len(df) == 0:
        return {
            "error": "Dataset is empty",
            "count": 0
        }

    anomalies = df['annual_anomaly'].values
    years = df['year'].values

    mean_val = float(np.mean(anomalies))
    std_val = float(np.std(anomalies, ddof=1)) if len(anomalies) > 1 else 0.0
    median_val = float(np.median(anomalies))
    min_val = float(np.min(anomalies))
    max_val = float(np.max(anomalies))
    min_year = int(years[np.argmin(anomalies)])
    max_year = int(years[np.argmax(anomalies)])
    
    # 25th and 75th percentiles (IQR)
    q25, q75 = np.percentile(anomalies, [25, 75])
    iqr_val = float(q75 - q25)

    return {
        "count": int(len(df)),
        "start_year": int(years[0]),
        "end_year": int(years[-1]),
        "mean": round(mean_val, 4),
        "median": round(median_val, 4),
        "std_dev": round(std_val, 4),
        "min_anomaly": round(min_val, 4),
        "min_year": min_year,
        "max_anomaly": round(max_val, 4),
        "max_year": max_year,
        "iqr": round(iqr_val, 4),
        "q25": round(float(q25), 4),
        "q75": round(float(q75), 4)
    }


def calculate_linear_trend(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Computes Ordinary Least Squares (OLS) linear regression trend line.
    y = m * x + c
    Returns slope (°C/year), decadal warming rate (°C/decade), intercept, R-squared, and formula.
    """
    if df is None or len(df) < 2:
        return {
            "error": "At least 2 data points required for linear regression.",
            "slope_per_year": 0.0,
            "warming_rate_per_decade": 0.0,
            "r_squared": 0.0
        }

    x = df['year'].values.astype(float)
    y = df['annual_anomaly'].values.astype(float)
    n = len(x)

    x_mean = np.mean(x)
    y_mean = np.mean(y)

    # Numerator & Denominator for slope
    num = np.sum((x - x_mean) * (y - y_mean))
    den = np.sum((x - x_mean) ** 2)

    if den == 0:
        slope = 0.0
        intercept = y_mean
        r_squared = 0.0
    else:
        slope = num / den
        intercept = y_mean - slope * x_mean

        y_pred = slope * x + intercept
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - y_mean) ** 2)

        r_squared = 1.0 - (ss_res / ss_tot) if ss_tot != 0 else 0.0
        r_squared = max(0.0, min(1.0, float(r_squared)))

    decadal_rate = slope * 10.0
    century_rate = slope * 100.0

    # Trend direction description
    if decadal_rate > 0.05:
        trend_direction = "Strong warming trend"
    elif decadal_rate > 0.01:
        trend_direction = "Moderate warming trend"
    elif decadal_rate < -0.05:
        trend_direction = "Strong cooling trend"
    elif decadal_rate < -0.01:
        trend_direction = "Moderate cooling trend"
    else:
        trend_direction = "Stable / negligible trend"

    return {
        "start_year": int(x[0]),
        "end_year": int(x[-1]),
        "sample_size": n,
        "slope_per_year": round(float(slope), 5),
        "warming_rate_per_decade": round(float(decadal_rate), 4),
        "warming_rate_per_century": round(float(century_rate), 3),
        "intercept": round(float(intercept), 4),
        "r_squared": round(float(r_squared), 4),
        "variance_explained_pct": round(float(r_squared) * 100, 2),
        "trend_direction": trend_direction,
        "formula": f"Anomaly = {slope:.5f} * (Year - {int(x_mean)}) + {y_mean:.4f}"
    }


def get_warmest_years(df: pd.DataFrame, n: int = 5) -> List[Dict[str, Any]]:
    """
    Returns the top N warmest years on record.
    """
    if df is None or len(df) == 0:
        return []
    n = max(1, min(n, len(df)))
    sorted_df = df.sort_values(by='annual_anomaly', ascending=False).head(n)
    
    results = []
    for rank, (_, row) in enumerate(sorted_df.iterrows(), start=1):
        results.append({
            "rank": rank,
            "year": int(row['year']),
            "anomaly": round(float(row['annual_anomaly']), 3),
            "uncertainty": round(float(row['uncertainty']), 3) if 'uncertainty' in row else 0.05
        })
    return results


def get_coldest_years(df: pd.DataFrame, n: int = 5) -> List[Dict[str, Any]]:
    """
    Returns the top N coldest years on record.
    """
    if df is None or len(df) == 0:
        return []
    n = max(1, min(n, len(df)))
    sorted_df = df.sort_values(by='annual_anomaly', ascending=True).head(n)
    
    results = []
    for rank, (_, row) in enumerate(sorted_df.iterrows(), start=1):
        results.append({
            "rank": rank,
            "year": int(row['year']),
            "anomaly": round(float(row['annual_anomaly']), 3),
            "uncertainty": round(float(row['uncertainty']), 3) if 'uncertainty' in row else 0.05
        })
    return results


def compare_periods(
    df: pd.DataFrame,
    period_a: Tuple[int, int],
    period_b: Tuple[int, int]
) -> Dict[str, Any]:
    """
    Compares two time intervals (e.g. baseline/historical vs modern era).
    Computes mean differences, standard deviations, and Cohen's d effect size.
    """
    a_start, a_end = sorted(period_a)
    b_start, b_end = sorted(period_b)

    df_a = df[(df['year'] >= a_start) & (df['year'] <= a_end)]
    df_b = df[(df['year'] >= b_start) & (df['year'] <= b_end)]

    if len(df_a) == 0 or len(df_b) == 0:
        return {
            "error": "One or both periods contain no data points in this dataset.",
            "period_a": {"start": a_start, "end": a_end, "count": len(df_a)},
            "period_b": {"start": b_start, "end": b_end, "count": len(df_b)}
        }

    vals_a = df_a['annual_anomaly'].values
    vals_b = df_b['annual_anomaly'].values

    mean_a = float(np.mean(vals_a))
    mean_b = float(np.mean(vals_b))
    std_a = float(np.std(vals_a, ddof=1)) if len(vals_a) > 1 else 0.001
    std_b = float(np.std(vals_b, ddof=1)) if len(vals_b) > 1 else 0.001

    diff = mean_b - mean_a

    # Pooled standard deviation & Cohen's d
    n_a, n_b = len(vals_a), len(vals_b)
    if n_a + n_b > 2:
        pooled_var = (((n_a - 1) * (std_a ** 2)) + ((n_b - 1) * (std_b ** 2))) / (n_a + n_b - 2)
        pooled_sd = np.sqrt(max(1e-6, pooled_var))
        cohens_d = diff / pooled_sd
    else:
        pooled_sd = max(std_a, std_b)
        cohens_d = diff / (pooled_sd if pooled_sd > 0 else 1.0)

    # Effect size magnitude
    d_abs = abs(cohens_d)
    if d_abs >= 0.8:
        effect_label = "Large effect / substantial shift"
    elif d_abs >= 0.5:
        effect_label = "Medium effect / notable shift"
    elif d_abs >= 0.2:
        effect_label = "Small effect / minor shift"
    else:
        effect_label = "Negligible effect / consistent with natural baseline"

    return {
        "period_a": {
            "label": f"{a_start}–{a_end}",
            "start_year": a_start,
            "end_year": a_end,
            "count": n_a,
            "mean_anomaly": round(mean_a, 4),
            "std_dev": round(std_a, 4)
        },
        "period_b": {
            "label": f"{b_start}–{b_end}",
            "start_year": b_start,
            "end_year": b_end,
            "count": n_b,
            "mean_anomaly": round(mean_b, 4),
            "std_dev": round(std_b, 4)
        },
        "absolute_difference_c": round(diff, 4),
        "cohens_d": round(float(cohens_d), 3),
        "effect_label": effect_label,
        "direction": "warmer" if diff > 0 else ("cooler" if diff < 0 else "identical")
    }


def calculate_decadal_averages(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Calculates aggregated temperature anomalies grouped by decade.
    """
    if df is None or len(df) == 0:
        return []

    temp_df = df.copy()
    temp_df['decade'] = (temp_df['year'] // 10) * 10

    grouped = temp_df.groupby('decade').agg(
        mean_anomaly=('annual_anomaly', 'mean'),
        std_dev=('annual_anomaly', 'std'),
        count=('annual_anomaly', 'count'),
        min_anomaly=('annual_anomaly', 'min'),
        max_anomaly=('annual_anomaly', 'max')
    ).reset_index()

    decades_list = []
    for _, row in grouped.iterrows():
        dec_int = int(row['decade'])
        decades_list.append({
            "decade": f"{dec_int}s",
            "start_year": dec_int,
            "end_year": dec_int + 9,
            "count": int(row['count']),
            "mean_anomaly": round(float(row['mean_anomaly']), 4),
            "std_dev": round(float(row['std_dev']), 4) if not pd.isna(row['std_dev']) else 0.0,
            "min_anomaly": round(float(row['min_anomaly']), 4),
            "max_anomaly": round(float(row['max_anomaly']), 4)
        })

    return decades_list


def assess_data_quality(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Audits dataset completeness, continuity, and observational uncertainty.
    """
    if df is None or len(df) == 0:
        return {"error": "Dataset is empty"}

    years = df['year'].values
    min_year = int(years[0])
    max_year = int(years[-1])
    expected_years = set(range(min_year, max_year + 1))
    actual_years = set(years)
    missing_years = sorted(list(expected_years - actual_years))

    mean_unc = float(df['uncertainty'].mean()) if 'uncertainty' in df else 0.05
    max_unc = float(df['uncertainty'].max()) if 'uncertainty' in df else 0.05
    min_unc = float(df['uncertainty'].min()) if 'uncertainty' in df else 0.05

    completeness_pct = (len(actual_years) / len(expected_years)) * 100 if len(expected_years) > 0 else 100.0

    return {
        "total_records": len(df),
        "span_years": max_year - min_year + 1,
        "start_year": min_year,
        "end_year": max_year,
        "missing_years_count": len(missing_years),
        "missing_years_list": missing_years,
        "temporal_completeness_pct": round(completeness_pct, 2),
        "average_uncertainty_c": round(mean_unc, 4),
        "min_uncertainty_c": round(min_unc, 4),
        "max_uncertainty_c": round(max_unc, 4),
        "quality_rating": "High (continuous annual records)" if len(missing_years) == 0 else "Moderate (interrupted)"
    }
