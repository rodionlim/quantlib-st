"""

GENERAL CONSTANTS

"""

import datetime
import pandas as pd

from enum import Enum

CALENDAR_DAYS_IN_YEAR = 365.25

BUSINESS_DAYS_IN_YEAR = 256.0
ROOT_BDAYS_INYEAR = BUSINESS_DAYS_IN_YEAR**0.5

WEEKS_IN_YEAR = CALENDAR_DAYS_IN_YEAR / 7.0

MONTHS_IN_YEAR = 12.0

HOURS_PER_DAY = 24
MINUTES_PER_HOUR = 60
SECONDS_PER_MINUTE = 60
SECONDS_PER_HOUR = MINUTES_PER_HOUR * SECONDS_PER_MINUTE
SECONDS_PER_DAY = HOURS_PER_DAY * SECONDS_PER_HOUR
SECONDS_IN_YEAR = CALENDAR_DAYS_IN_YEAR * SECONDS_PER_DAY

ARBITRARY_START = datetime.datetime(1900, 1, 1)

NOTIONAL_CLOSING_TIME_AS_PD_OFFSET = pd.DateOffset(
    hours=23,
    minutes=0,
    seconds=0,
)

"""

    FREQUENCIES

"""

Frequency = Enum(
    "Frequency",
    "Unknown Year Month Week BDay Day Hour Minutes_15 Minutes_5 Minute Seconds_10 Second Mixed",
)
DAILY_PRICE_FREQ = Frequency.Day
BUSINESS_DAY_FREQ = Frequency.BDay
HOURLY_FREQ = Frequency.Hour

MIXED_FREQ = Frequency.Mixed


def from_config_frequency_pandas_resample(freq: Frequency) -> str:
    """
    Translate between Frequency and pandas resample strings.
    """

    LOOKUP_TABLE = {
        Frequency.BDay: "B",
        Frequency.Week: "W",
        Frequency.Month: "M",
        Frequency.Year: "A",
        Frequency.Day: "D",
    }

    try:
        resample_string = LOOKUP_TABLE[freq]
    except KeyError as exc:
        raise ValueError("Resample frequency %s is not supported" % freq) from exc

    return resample_string


def from_frequency_to_times_per_year(freq: Frequency) -> float:
    """
    Times a year that a frequency corresponds to
    """

    LOOKUP_TABLE = {
        Frequency.BDay: BUSINESS_DAYS_IN_YEAR,
        Frequency.Week: WEEKS_IN_YEAR,
        Frequency.Month: MONTHS_IN_YEAR,
        Frequency.Year: 1,
        Frequency.Day: CALENDAR_DAYS_IN_YEAR,
    }

    try:
        times_per_year = LOOKUP_TABLE[freq]
    except KeyError as exc:
        raise ValueError("Frequency %s is not supported" % freq) from exc

    return float(times_per_year)


"""
    
    EQUAL DATES WITHIN A YEAR

"""


def generate_equal_dates_within_year(
    year: int, number_of_dates: int, force_start_year_align: bool = False
) -> list[datetime.datetime]:
    """
    Generate equally spaced datetimes within a given year
    >>> generate_equal_dates_within_year(2022,3)
    [datetime.datetime(2022, 3, 2, 0, 0), datetime.datetime(2022, 7, 1, 0, 0), datetime.datetime(2022, 10, 30, 0, 0)]
    >>> generate_equal_dates_within_year(2022,1)
    [datetime.datetime(2022, 7, 2, 0, 0)]
    >>> generate_equal_dates_within_year(2021,2, force_start_year_align=True)
    [datetime.datetime(2021, 1, 1, 0, 0), datetime.datetime(2021, 7, 2, 0, 0)]
    """

    days_between_periods = int(CALENDAR_DAYS_IN_YEAR / float(number_of_dates))
    first_date = _calculate_first_date_for_equal_dates(
        year=year,
        days_between_periods=days_between_periods,
        force_start_year_align=force_start_year_align,
    )
    delta_for_each_period = datetime.timedelta(days=days_between_periods)

    all_dates = [
        first_date + (delta_for_each_period * period_count)
        for period_count in range(number_of_dates)
    ]

    return all_dates


def _calculate_first_date_for_equal_dates(
    year: int, days_between_periods: int, force_start_year_align: bool = False
) -> datetime.datetime:
    start_of_year = datetime.datetime(year, 1, 1)

    if force_start_year_align:
        ## more realistic for most rolling calendars
        first_date = start_of_year
    else:
        half_period = int(days_between_periods / 2)
        half_period_increment = datetime.timedelta(days=half_period)
        first_date = start_of_year + half_period_increment

    return first_date


"""

    FUTURES MONTHS

"""

FUTURES_MONTH_LIST = ["F", "G", "H", "J", "K", "M", "N", "Q", "U", "V", "X", "Z"]


def month_from_contract_letter(contract_letter: str) -> int:
    """
    Returns month number (1 is January) from contract letter
    >>> month_from_contract_letter("F")
    1
    >>> month_from_contract_letter("Z")
    12
    >>> month_from_contract_letter("A")
    Exception: Contract letter A is not a valid future month (must be one of ['F', 'G', 'H', 'J', 'K', 'M', 'N', 'Q', 'U', 'V', 'X', 'Z'])

    """

    try:
        month_number = FUTURES_MONTH_LIST.index(contract_letter)
    except ValueError:
        raise Exception(
            "Contract letter %s is not a valid future month (must be one of %s)"
            % (contract_letter, str(FUTURES_MONTH_LIST))
        )

    return month_number + 1


def contract_month_from_number(month_number: int) -> str:
    """
    Returns standard month letters used in futures land

    >>> contract_month_from_number(1)
    'F'
    >>> contract_month_from_number(12)
    'Z'
    >>> contract_month_from_number(0)
    Exception: Months have to be between 1 and 12
    >>> contract_month_from_number(13)
    Exception: Months have to be between 1 and 12

    :param month_number: int
    :return: str
    """

    try:
        assert month_number > 0 and month_number < 13
    except:
        raise Exception("Months have to be between 1 and 12")

    return FUTURES_MONTH_LIST[month_number - 1]
