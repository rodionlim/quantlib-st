import numpy as np
import pandas as pd

from quantlib_st.core.algos.forecast import DefaultForecastAlgo


def test_calc_ewmac_forecast_minimal():
    rng = pd.date_range("2021-01-01", periods=11, freq="B")
    prices = pd.Series(100.0 + np.arange(len(rng)), index=rng)

    fcast = DefaultForecastAlgo.calc_ewmac_forecast(prices, Lfast=3)

    assert isinstance(fcast, pd.Series)
    # index should be business days (same as input here)
    assert fcast.index.equals(prices.resample("1B").last().index)
    # with 11 points we should get at least one finite value once vol is computed
    assert fcast.dropna().shape[0] >= 1
