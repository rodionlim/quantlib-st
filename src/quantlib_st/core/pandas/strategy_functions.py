from typing import Union

import pandas as pd

from quantlib_st.core.dateutils import SECONDS_IN_YEAR


def drawdown(x: Union[pd.DataFrame, pd.Series]) -> Union[pd.DataFrame, pd.Series]:
    """
    Returns a time series of drawdowns for a time series x.
    """
    maxx = x.expanding(min_periods=1).max()
    return x - maxx


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
