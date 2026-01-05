import datetime
import numpy as np
import pandas as pd

from quantlib_st.correlation.exponential_correlation import (
    ExponentialCorrelationResults,
    CorrelationEstimate,
)


def test_exponential_correlation_results_structure():
    # Create dummy returns for 3 instruments over 5 days
    dates = pd.date_range("2023-01-01", periods=5)
    data = pd.DataFrame(np.random.randn(5, 3), index=dates, columns=["A", "B", "C"])

    # Initialize with a small lookback for testing
    results = ExponentialCorrelationResults(data, ew_lookback=5, min_periods=2)

    # 1. Understanding _raw_correlations
    # When we call .corr(pairwise=True) on an EWM object, pandas returns a MultiIndex DataFrame.
    # Level 0: Date
    # Level 1: Instrument name
    raw = results.raw_correlations

    assert isinstance(raw, pd.DataFrame)
    # For 5 days and 3 instruments, we expect 5 * 3 = 15 rows
    assert len(raw) == 15
    # The columns should match the instrument names
    assert list(raw.columns) == ["A", "B", "C"]

    # Check the first date's matrix (it should be NaN if min_periods=2)
    first_date = dates[0]
    matrix_at_t0 = raw.loc[first_date]
    assert matrix_at_t0.isna().all().all()

    # Check the third date's matrix (should have values)
    third_date = dates[2]
    matrix_at_t2 = raw.loc[third_date]
    assert not matrix_at_t2.isna().any().any()
    assert matrix_at_t2.loc["A", "A"] == 1.0  # Diagonal is always 1.0


def test_last_valid_cor_matrix_for_date():
    dates = pd.date_range("2023-01-01", periods=10)
    data = pd.DataFrame(np.random.randn(10, 2), index=dates, columns=["X", "Y"])

    results = ExponentialCorrelationResults(data, ew_lookback=5, min_periods=2)

    # Test retrieving matrix for a specific point in time
    # If we ask for 2023-01-05, it should give us the matrix from the last available date BEFORE 2023-01-05
    target_date = datetime.datetime(2023, 1, 5)
    estimate = results.last_valid_cor_matrix_for_date(target_date)

    assert isinstance(estimate, CorrelationEstimate)
    assert estimate.columns == ["X", "Y"]
    assert estimate.values.shape == (2, 2)

    # The values should match the raw correlation at 2023-01-04
    expected_values = np.asarray(
        results.raw_correlations.loc[pd.Timestamp("2023-01-04")].values
    )
    np.testing.assert_array_almost_equal(estimate.values, expected_values)


def test_last_valid_cor_matrix_no_data():
    # Test what happens if we ask for a date before any data exists
    dates = pd.date_range("2023-01-10", periods=5)
    data = pd.DataFrame(np.random.randn(5, 2), index=dates, columns=["X", "Y"])
    results = ExponentialCorrelationResults(data)

    early_date = datetime.datetime(2023, 1, 1)
    estimate = results.last_valid_cor_matrix_for_date(early_date)

    # Should return a matrix of NaNs
    assert np.isnan(estimate.values).all()
