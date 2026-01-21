import pandas as pd
import numpy as np
import pytest

from livestock_project.project import (
    calculate_herd_structure,
    calculate_productivity_metrics,
    evaluate_sustainability,
    Herd
)

# -----------------------------
# Fixtures
# -----------------------------
@pytest.fixture
def sample_df():
    return pd.DataFrame({
        "sex": ["F", "M", "F"],
        "birth_date": pd.to_datetime([
            "2020-01-01",
            "2021-01-01",
            "2022-01-01"
        ]),
        "exit_date": pd.to_datetime([
            None,
            "2023-01-01",
            None
        ]),
        "weight_birth_kg": [35, 40, 38],
        "weight_last_kg": [350, 420, np.nan],
        "last_weight_date": pd.to_datetime([
            "2022-12-31",
            "2023-01-01",
            None
        ])
    })


# -----------------------------
# Herd structure tests
# -----------------------------
def test_calculate_herd_structure_basic(sample_df):
    result = calculate_herd_structure(sample_df)

    assert result["total_animals"] == 3
    assert result["pct_females"] == pytest.approx(66.67, rel=1e-2)
    assert result["pct_males"] == pytest.approx(33.33, rel=1e-2)
    assert result["avg_age_years"] > 0


def test_calculate_herd_structure_empty():
    df = pd.DataFrame()
    result = calculate_herd_structure(df)

    assert result["total_animals"] == 0
    assert result["pct_females"] == 0.0
    assert result["pct_males"] == 0.0
    assert np.isnan(result["avg_age_years"])


# -----------------------------
# Productivity metrics tests
# -----------------------------
def test_calculate_productivity_metrics(sample_df):
    result = calculate_productivity_metrics(sample_df)

    assert result["pct_complete_weight_records"] > 0
    assert result["avg_daily_gain_kg_day"] > 0
    assert result["mean_age_at_exit_years"] > 0


def test_calculate_productivity_metrics_no_valid_weights():
    df = pd.DataFrame({
        "birth_date": pd.to_datetime(["2020-01-01"]),
        "exit_date": pd.to_datetime(["2021-01-01"]),
        "weight_birth_kg": [np.nan],
        "weight_last_kg": [np.nan],
        "last_weight_date": [None]
    })

    result = calculate_productivity_metrics(df)

    assert np.isnan(result["avg_daily_gain_kg_day"])
    assert result["pct_complete_weight_records"] == 0.0


# -----------------------------
# Herd class tests
# -----------------------------
def test_total_livestock_units(sample_df):
    herd = Herd(sample_df)
    lu = herd.total_livestock_units(only_active=True)

    assert lu > 0
    assert isinstance(lu, float)


def test_total_livestock_units_empty():
    herd = Herd(pd.DataFrame())
    assert herd.total_livestock_units() == 0.0


# -----------------------------
# Sustainability tests
# -----------------------------
def test_evaluate_sustainability_ok(sample_df):
    result = evaluate_sustainability(
        df=sample_df,
        farm_area_ha=200,
        max_lu_per_ha=1.0
    )

    assert result["sustainability_status"] == "OK"


def test_evaluate_sustainability_invalid_area(sample_df):
    with pytest.raises(ValueError):
        evaluate_sustainability(
            df=sample_df,
            farm_area_ha=0,
            max_lu_per_ha=0.6
        )
