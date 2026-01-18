import datetime
import numpy as np
import pandas as pd

from typing import Union

from quantlib_st.core.constants import named_object
from quantlib_st.core.dateutils import (
    Frequency,
    BUSINESS_DAY_FREQ,
    BUSINESS_DAYS_IN_YEAR,
    CALENDAR_DAYS_IN_YEAR,
    HOURLY_FREQ,
    HOURS_PER_DAY,
    NOTIONAL_CLOSING_TIME_AS_PD_OFFSET,
)


def resample_prices_to_business_day_index(x: pd.Series) -> pd.Series:
    """Resample prices to a business-day index by taking the last available price.

    This groups the input `Series` into business-day bins (frequency "1B") and returns the
    *last* observed value within each business day. If there are no observations for a
    given business day (for example, the series has data up to Thursday but none on Friday),
    the result for that day will be ``NaN`` — the function does **not** forward-fill missing
    days automatically.

    This is useful for ensuring that price series align with business-day calendars, across
    all instruments.
    """
    return x.resample("1B").last()


def get_intraday_pdf_at_frequency(
    pd_object: Union[pd.DataFrame, pd.Series],
    frequency: str = "H",
    closing_time: pd.DateOffset = NOTIONAL_CLOSING_TIME_AS_PD_OFFSET,
) -> Union[pd.Series, pd.DataFrame]:
    """
    >>> import datetime
    >>> d = datetime.datetime
    >>> date_index = [d(2000,1,1,15),d(2000,1,1,16),d(2000,1,1,23), d(2000,1,2,15)]
    >>> df = pd.DataFrame(dict(a=[1, 2, 3,4], b=[4,5,6,7]), index=date_index)
    >>> get_intraday_pdf_at_frequency(df,"2H")
                           a    b
    2000-01-01 14:00:00  1.0  4.0
    2000-01-01 16:00:00  2.0  5.0
    2000-01-02 14:00:00  4.0  7.0
    """
    intraday_only_df = intraday_date_rows_in_pd_object(
        pd_object, closing_time=closing_time
    )
    intraday_df = intraday_only_df.resample(frequency).last()
    intraday_df_clean = intraday_df.dropna()

    return intraday_df_clean


def intraday_date_rows_in_pd_object(
    pd_object: Union[pd.DataFrame, pd.Series],
    closing_time: pd.DateOffset = NOTIONAL_CLOSING_TIME_AS_PD_OFFSET,
) -> Union[pd.DataFrame, pd.Series]:
    """
    >>> import datetime
    >>> d = datetime.datetime
    >>> date_index = [d(2000,1,1,15),d(2000,1,1,23), d(2000,1,2,15)]
    >>> df = pd.DataFrame(dict(a=[1, 2, 3], b=[4 , 6, 5]), index=date_index)
    >>> intraday_date_rows_in_pd_object(df)
                         a  b
    2000-01-01 15:00:00  1  4
    2000-01-02 15:00:00  3  5
    """

    return pd_object[
        [
            not check_time_matches_closing_time_to_second(
                index_entry=index_entry, closing_time=closing_time
            )
            for index_entry in pd_object.index
        ]
    ]


def check_time_matches_closing_time_to_second(
    index_entry: datetime.datetime,
    closing_time: pd.DateOffset = NOTIONAL_CLOSING_TIME_AS_PD_OFFSET,
) -> bool:
    """
    Check time matches at one second resolution (good enough)

    >>> check_time_matches_closing_time_to_second(datetime.datetime(2023, 1, 15, 6, 32))
    False
    >>> check_time_matches_closing_time_to_second(datetime.datetime(2023, 1, 15, 23, 0))
    True
    """

    if (
        index_entry.hour == closing_time.hours  # type: ignore
        and index_entry.minute == closing_time.minutes  # type: ignore
        and index_entry.second == closing_time.seconds  # type: ignore
    ):
        return True
    else:
        return False


def infer_frequency(
    df_or_ts: Union[pd.DataFrame, pd.Series] | named_object,
) -> Frequency:
    if df_or_ts is named_object:
        raise Exception("Cannot infer frequency when args is not supplied")

    inferred = pd.infer_freq(df_or_ts.index)  # type: ignore
    if inferred is None:
        assert df_or_ts is pd.DataFrame or df_or_ts is pd.Series
        return infer_frequency_approx(df_or_ts)
    if inferred == "B":
        return BUSINESS_DAY_FREQ
    if inferred == "H":
        return HOURLY_FREQ
    raise Exception("Frequency of time series unknown")


UPPER_BOUND_HOUR_FRACTION_OF_A_DAY = 1.0 / 2.0
LOWER_BOUND_HOUR_FRACTION_OF_A_DAY = 1.0 / HOURS_PER_DAY
BUSINESS_CALENDAR_FRACTION = CALENDAR_DAYS_IN_YEAR / BUSINESS_DAYS_IN_YEAR


def infer_frequency_approx(df_or_ts: Union[pd.DataFrame, pd.Series]) -> Frequency:
    avg_time_delta_in_days = average_time_delta_for_time_series(df_or_ts)

    if _probably_daily_freq(avg_time_delta_in_days):
        return BUSINESS_DAY_FREQ

    if _probably_hourly_freq(avg_time_delta_in_days):
        return HOURLY_FREQ

    raise Exception("Can't work out approximate frequency")


def _probably_daily_freq(avg_time_delta_in_days: float) -> bool:
    return round(avg_time_delta_in_days, 1) == BUSINESS_CALENDAR_FRACTION


def _probably_hourly_freq(avg_time_delta_in_days: float) -> bool:
    return (avg_time_delta_in_days < UPPER_BOUND_HOUR_FRACTION_OF_A_DAY) & (
        avg_time_delta_in_days >= LOWER_BOUND_HOUR_FRACTION_OF_A_DAY
    )


def average_time_delta_for_time_series(
    df_or_ts: Union[pd.DataFrame, pd.Series],
) -> float:
    avg_time_delta = abs(np.diff(df_or_ts.index)).mean()
    avg_time_delta_in_days = avg_time_delta / np.timedelta64(1, "D")

    return avg_time_delta_in_days
