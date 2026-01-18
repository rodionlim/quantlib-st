from copy import copy
from typing import Union

import pandas as pd
import numpy as np

from quantlib_st.core.dateutils import BUSINESS_DAYS_IN_YEAR, SECONDS_IN_YEAR


def turnover(
    x: pd.Series, y: Union[pd.Series, float, int], smooth_y_days: int = 250
) -> float:
    """
    Calculates the annualized turnover of a series 'x', normalized by a scale 'y'.

    This is typically used to measure how much a signal or position changes over time,
    independent of the absolute size of the position or the risk target.

    Process:
    1. Resamples 'x' to business days.
    2. Normalizes 'x' by dividing by 'y' (the 'scale'). If 'y' is a series, it is
       smoothed with an EWMA to avoid capturing noise in the risk target itself.
    3. Calculates the average absolute daily change of this normalized series.
    4. Multiplies by BUSINESS_DAYS_IN_YEAR (256) to return an annualized figure.

    A turnover of 2.0 means the system trades twice its average position size
    per year.

    :param x: The series to measure (e.g. position size or forecast)
    :param y: The normalization factor (e.g. target risk or constant scalar)
    :param smooth_y_days: Lookback for smoothing 'y' if it is a series.
    :return: Annualized turnover (float)
    """

    daily_x = x.resample("1B").last()
    if isinstance(y, float) or isinstance(y, int):
        daily_y = pd.Series(np.full(daily_x.shape[0], float(y)), daily_x.index)
    else:
        daily_y = y.reindex(daily_x.index, method="ffill")
        ## need to apply a drag to this or will give zero turnover for constant risk
        daily_y = daily_y.ewm(smooth_y_days, min_periods=2).mean()

    x_normalised_for_y = daily_x / daily_y.ffill()

    avg_daily = float(x_normalised_for_y.diff().abs().mean())

    return avg_daily * BUSINESS_DAYS_IN_YEAR


def drawdown(x: Union[pd.DataFrame, pd.Series]) -> Union[pd.DataFrame, pd.Series]:
    """
    Returns a time series of drawdowns for a time series x.
    """
    maxx = x.expanding(min_periods=1).max()
    return x - maxx


def apply_abs_min(x: pd.Series, min_value: float = 0.1) -> pd.Series:
    """
    >>> import datetime
    >>> from syscore.pandas.pdutils import create_arbitrary_pdseries
    >>> s1=create_arbitrary_pdseries([1,2,3,-1,-2,-3], date_start = datetime.datetime(2000,1,1))
    >>> apply_abs_min(s1, 2)
    2000-01-03    2
    2000-01-04    2
    2000-01-05    3
    2000-01-06   -2
    2000-01-07   -2
    2000-01-10   -3
    Freq: B, dtype: int64
    """

    ## Could also use clip but no quicker and this is more intuitive
    x[(x < min_value) & (x > 0)] = min_value
    x[(x > -min_value) & (x < 0)] = -min_value

    return x


def spread_out_annualised_return_over_periods(data_as_annual: pd.Series) -> pd.Series:
    """
    Spread an annualised return series into per-period returns.
    """
    period_intervals_in_seconds = (
        data_as_annual.index.to_series().diff().dt.total_seconds()  # type: ignore
    )
    period_intervals_in_year_fractions = period_intervals_in_seconds / SECONDS_IN_YEAR
    data_per_period = data_as_annual * period_intervals_in_year_fractions

    return data_per_period


def replace_all_zeros_with_nan(pd_series: pd.Series) -> pd.Series:
    """
    >>> import datetime
    >>> d = datetime.datetime
    >>> date_index1 = [d(2000,1,1,23),d(2000,1,2,23),d(2000,1,3,23)]
    >>> s1 = pd.Series([0,5,6], index=date_index1)
    >>> replace_all_zeros_with_nan(s1)
    2000-01-01 23:00:00    NaN
    2000-01-02 23:00:00    5.0
    2000-01-03 23:00:00    6.0
    dtype: float64
    """
    copy_pd_series = copy(pd_series)
    copy_pd_series[copy_pd_series == 0.0] = np.nan

    if all(copy_pd_series.isna()):
        copy_pd_series[:] = np.nan

    return copy_pd_series


def calculate_cost_deflator(price: pd.Series) -> pd.Series:
    daily_returns = price_to_daily_returns(price)
    ## crude but doesn't matter
    vol_price = daily_returns.rolling(180, min_periods=3).std().ffill()
    final_vol = vol_price.iloc[-1]

    cost_scalar = vol_price / final_vol

    return cost_scalar


def price_to_daily_returns(price: pd.Series) -> pd.Series:
    daily_price = price.resample("1B").ffill()
    daily_returns = daily_price.ffill().diff()

    return daily_returns


def years_in_data(data: pd.Series) -> list[int]:
    """
    >>> import datetime
    >>> d = datetime.datetime
    >>> date_index1 = [d(2000,1,1),d(2002,1,2),d(2003,1,5)]
    >>> s1 = pd.Series([1,2,3], index=date_index1)
    >>> years_in_data(s1)
    [2000, 2002, 2003]
    """

    all_years = [x.year for x in data.index]
    unique_years = list(set(all_years))
    unique_years.sort()

    return unique_years


if __name__ == "__main__":
    import doctest

    doctest.testmod()
