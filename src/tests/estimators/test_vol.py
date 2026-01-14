import numpy as np
import pandas as pd

from quantlib_st.estimators.vol import robust_vol_calc, mixed_vol_calc


def test_robust_vol_calc_basic():
    rng = pd.date_range("2020-01-01", periods=50, freq="B")
    np.random.seed(0)
    returns = pd.Series(0.001 * np.random.randn(len(rng)), index=rng)

    vol = robust_vol_calc(
        returns, days=10, min_periods=5, vol_abs_min=1e-10, vol_floor=False
    )

    assert isinstance(vol, pd.Series)
    assert vol.index.equals(returns.index)
    # values that are not NaN should be at least the absolute min
    assert (vol.dropna() >= 1e-10).all()
    # first (min_periods - 1) values should be NaN due to min_periods
    assert vol.iloc[:4].isna().all()


def test_mixed_vol_calc_basic():
    rng = pd.date_range("2020-01-01", periods=60, freq="B")
    np.random.seed(1)
    returns = pd.Series(0.001 * np.random.randn(len(rng)), index=rng)

    vol = mixed_vol_calc(
        returns,
        days=10,
        min_periods=5,
        slow_vol_years=2,
        proportion_of_slow_vol=0.3,
        vol_abs_min=1e-10,
    )

    assert isinstance(vol, pd.Series)
    assert vol.index.equals(returns.index)
    assert (vol.dropna() >= 1e-10).all()
