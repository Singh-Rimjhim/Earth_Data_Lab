"""
Unit tests for core.statistics_engine.
"""

import pytest
import pandas as pd
import numpy as np
from core.statistics_engine import (
    calculate_summary_statistics,
    calculate_linear_trend,
    get_warmest_years,
    get_coldest_years,
    compare_periods,
    calculate_decadal_averages,
    assess_data_quality
)


@pytest.fixture
def sample_climate_df():
    """Generates a small test dataframe with known properties."""
    data = {
        'year': [1980, 1981, 1982, 1983, 1984, 1985],
        'annual_anomaly': [0.10, 0.20, 0.15, 0.30, 0.25, 0.40],
        'five_year_smooth': [0.12, 0.18, 0.22, 0.26, 0.30, 0.34],
        'uncertainty': [0.05, 0.05, 0.05, 0.05, 0.05, 0.05]
    }
    return pd.DataFrame(data)


def test_calculate_summary_statistics(sample_climate_df):
    stats = calculate_summary_statistics(sample_climate_df)
    assert stats['count'] == 6
    assert stats['start_year'] == 1980
    assert stats['end_year'] == 1985
    assert pytest.approx(stats['mean'], 0.01) == 0.2333
    assert stats['min_anomaly'] == 0.10
    assert stats['min_year'] == 1980
    assert stats['max_anomaly'] == 0.40
    assert stats['max_year'] == 1985


def test_calculate_linear_trend(sample_climate_df):
    trend = calculate_linear_trend(sample_climate_df)
    # The anomalies are increasing: 0.10 to 0.40 over 5 years (~0.055 per year = ~0.55 per decade)
    assert trend['slope_per_year'] > 0
    assert trend['warming_rate_per_decade'] > 0.4
    assert trend['r_squared'] > 0.75
    assert "warming" in trend['trend_direction'].lower()


def test_get_warmest_years(sample_climate_df):
    warmest = get_warmest_years(sample_climate_df, n=3)
    assert len(warmest) == 3
    assert warmest[0]['year'] == 1985
    assert warmest[0]['anomaly'] == 0.40
    assert warmest[1]['year'] == 1983
    assert warmest[2]['year'] == 1984


def test_get_coldest_years(sample_climate_df):
    coldest = get_coldest_years(sample_climate_df, n=2)
    assert len(coldest) == 2
    assert coldest[0]['year'] == 1980
    assert coldest[0]['anomaly'] == 0.10
    assert coldest[1]['year'] == 1982
    assert coldest[1]['anomaly'] == 0.15


def test_compare_periods():
    data = {
        'year': [1900, 1901, 1902, 2000, 2001, 2002],
        'annual_anomaly': [-0.20, -0.25, -0.15, 0.60, 0.65, 0.70],
        'five_year_smooth': [-0.20, -0.20, -0.20, 0.65, 0.65, 0.65],
        'uncertainty': [0.10, 0.10, 0.10, 0.05, 0.05, 0.05]
    }
    df = pd.DataFrame(data)
    comp = compare_periods(df, (1900, 1902), (2000, 2002))
    assert comp['direction'] == 'warmer'
    assert comp['absolute_difference_c'] > 0.8
    assert comp['cohens_d'] > 2.0


def test_calculate_decadal_averages(sample_climate_df):
    decades = calculate_decadal_averages(sample_climate_df)
    assert len(decades) == 1
    assert decades[0]['decade'] == '1980s'
    assert decades[0]['count'] == 6


def test_assess_data_quality(sample_climate_df):
    quality = assess_data_quality(sample_climate_df)
    assert quality['total_records'] == 6
    assert quality['temporal_completeness_pct'] == 100.0
    assert quality['missing_years_count'] == 0
