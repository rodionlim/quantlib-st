import pandas as pd
import numpy as np

from quantlib_st.systems.accounts.account_forecast import pandl_for_instrument_forecast
from quantlib_st.systems.accounts.curves.account_curve import accountCurve


def test_pandl_for_instrument_forecast_basic():
    # Setup dummy data
    # Constant price of 100 over 10 days
    dates = pd.date_range("2023-01-01", periods=10, freq="B")
    price = pd.Series([100.0] * 10, index=dates)

    # Constant forecast of 10 (which is the default target_abs_forecast)
    # This should result in a normalization factor of 1.0
    forecast = pd.Series([10.0] * 10, index=dates)

    # Mock volatility to make calculations predictable
    # If we don't provide it, it will be calculated from prices
    # Robust daily vol for a constant series might be small or zero,
    # so we provide a fixed value.
    daily_returns_volatility = pd.Series([1.0] * 10, index=dates)

    capital = 100000.0
    risk_target = 0.16

    # Run the function
    result = pandl_for_instrument_forecast(
        forecast=forecast,
        price=price,
        capital=capital,
        risk_target=risk_target,
        daily_returns_volatility=daily_returns_volatility,
        target_abs_forecast=10.0,
        value_per_point=1.0,
    )

    # Assertions
    # 1. Check return type
    assert isinstance(result, accountCurve)

    # 2. Check the flow results in the expected position size
    # Daily risk target = 0.16 / sqrt(252)
    # Root bdays in year is typically 15.8745...
    from quantlib_st.core.dateutils import ROOT_BDAYS_INYEAR

    daily_risk_target = risk_target / ROOT_BDAYS_INYEAR
    daily_cash_vol_target = capital * daily_risk_target

    # Average notional position = daily_cash_vol_target / (vol * value_per_point)
    # With vol=1.0 and value_per_point=1.0:
    expected_avg_position = daily_cash_vol_target / (1.0 * 1.0)

    # Normalized forecast = 10 / 10 = 1.0
    # Final position = 1.0 * expected_avg_position

    # The accountCurve stores the P&L, but we can verify the sizing logic by checking the internal state
    # if we exposed it, but pandl_for_instrument_forecast returns the final curve.

    # For a constant price and no costs, the P&L should be zero
    # (P&L = position * price_change)
    assert (result == 0).all()


def test_pandl_for_instrument_forecast_scaling():
    """Test that doubling the forecast doubles the resulting P&L (without costs)"""
    dates = pd.date_range("2023-01-01", periods=10, freq="B")
    # We need some price movement to see P&L
    price = pd.Series([100, 101, 102, 101, 100, 101, 102, 103, 102, 101], index=dates)
    daily_returns_volatility = pd.Series([1.0] * 10, index=dates)

    forecast_10 = pd.Series([10.0] * 10, index=dates)
    forecast_20 = pd.Series([20.0] * 10, index=dates)

    res_10 = pandl_for_instrument_forecast(
        forecast=forecast_10,
        price=price,
        daily_returns_volatility=daily_returns_volatility,
    )

    res_20 = pandl_for_instrument_forecast(
        forecast=forecast_20,
        price=price,
        daily_returns_volatility=daily_returns_volatility,
    )

    # Since forecast 20 is exactly double of forecast 10, and target is 10,
    # the normalized forecast is 2.0 vs 1.0.
    # Therefore the position is doubled, and the P&L should be doubled.
    # Note: Arithmetic operations on accountCurve currently return a base pd.Series
    np.testing.assert_allclose(res_20.values, (res_10 * 2.0).values)  # type: ignore
    assert isinstance(res_10, accountCurve)
    assert isinstance(res_20, accountCurve)
