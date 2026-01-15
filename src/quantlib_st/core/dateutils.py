"""

GENERAL CONSTANTS

"""

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


Frequency = Enum(
    "Frequency",
    "Unknown Year Month Week BDay Day",
)

DAILY_PRICE_FREQ = Frequency.Day


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
