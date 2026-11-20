"""
Unit tests for core.assistant.
"""

import pytest
from core.data_loader import DataLoader
from core.assistant import ClimateAssistant


@pytest.fixture
def assistant_instance():
    loader = DataLoader()
    return ClimateAssistant(loader)


def test_intent_detection(assistant_instance):
    assert assistant_instance.detect_intent("Is the Earth warming?") == "TREND_ANALYSIS"
    assert assistant_instance.detect_intent("What is the rate of warming per decade?") == "TREND_ANALYSIS"
    assert assistant_instance.detect_intent("What are the top 5 warmest years?") == "WARMEST_COLDEST"
    assert assistant_instance.detect_intent("Coldest year on record") == "WARMEST_COLDEST"
    assert assistant_instance.detect_intent("Compare 1880-1920 with 1980-2020") == "PERIOD_COMPARISON"
    assert assistant_instance.detect_intent("What is the average anomaly in the 2000s?") == "AVERAGE_CALCULATION"
    assert assistant_instance.detect_intent("What is the temperature variability?") == "VARIABILITY_ANALYSIS"
    assert assistant_instance.detect_intent("What are the limitations of this data?") == "DATA_QUALITY"
    assert assistant_instance.detect_intent("Will it rain tomorrow in Paris?") == "OUT_OF_SCOPE"


def test_year_extraction(assistant_instance):
    years = assistant_instance.extract_years("Compare 1910 and 1990 data")
    assert years == [1910, 1990]


def test_top_n_extraction(assistant_instance):
    assert assistant_instance.extract_top_n("top 10 warmest years") == 10
    assert assistant_instance.extract_top_n("warmest years", default=5) == 5


def test_answer_query_warming(assistant_instance):
    res = assistant_instance.answer_query("Is the Earth warming?", "nasa_gistemp")
    assert res['intent'] == "TREND_ANALYSIS"
    assert "Warming Rate" in res['metrics']
    assert not res['is_synthetic']


def test_answer_query_synthetic(assistant_instance):
    res = assistant_instance.answer_query("Is the Earth warming?", "synthetic_demo")
    assert res['intent'] == "TREND_ANALYSIS"
    assert res['is_synthetic'] is True


def test_out_of_scope_query(assistant_instance):
    res = assistant_instance.answer_query("Will it rain tomorrow in Delhi?", "nasa_gistemp")
    assert res['intent'] == "OUT_OF_SCOPE"
    assert "Out of Scope" in res['answer']
