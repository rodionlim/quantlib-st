from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import List

import pandas as pd


IN_SAMPLE = "in_sample"
ROLLING = "rolling"
EXPANDING = "expanding"

POSSIBLE_DATE_METHODS = [IN_SAMPLE, ROLLING, EXPANDING]


@dataclass
class fitDates:
    fit_start: datetime.datetime
    fit_end: datetime.datetime
    period_start: datetime.datetime
    period_end: datetime.datetime
    no_data: bool = False


class listOfFittingDates(list):
    def list_of_starting_periods(self) -> list:
        return [period.period_start for period in self]

    def index_of_most_recent_period_before_relevant_date(
        self, relevant_date: datetime.datetime
    ):
        index = []
        list_of_start_periods = self.list_of_starting_periods()
        if relevant_date < list_of_start_periods[0]:
            raise Exception(f"Date {relevant_date} is before first fitting date")

        for index, start_date in enumerate(list_of_start_periods):
            if relevant_date < start_date:
                return index - 1

        return index


def generate_fitting_dates(
    data: pd.DataFrame,
    date_method: str,
    rollyears: int = 20,
    interval_frequency: str = "12M",
) -> listOfFittingDates:
    if date_method not in POSSIBLE_DATE_METHODS:
        raise ValueError(
            f"Unknown date_method={date_method}; expected one of {POSSIBLE_DATE_METHODS}"
        )

    start_date = data.index[0]
    end_date = data.index[-1]

    if date_method == IN_SAMPLE:
        return listOfFittingDates(
            [fitDates(start_date, end_date, start_date, end_date, no_data=False)]
        )

    boundaries = _list_of_starting_dates_per_period(
        start_date, end_date, interval_frequency=interval_frequency
    )

    # Short history: fall back to a single in-sample period.
    if len(boundaries) < 2:
        return listOfFittingDates(
            [fitDates(start_date, end_date, start_date, end_date, no_data=False)]
        )

    periods: List[fitDates] = []
    for period_index in range(len(boundaries))[1:-1]:
        period_start = boundaries[period_index]
        period_end = boundaries[period_index + 1]

        if date_method == EXPANDING:
            fit_start = start_date
        elif date_method == ROLLING:
            yearidx_to_use = max(0, period_index - rollyears)
            fit_start = boundaries[yearidx_to_use]
        else:
            raise ValueError(f"Unknown date_method={date_method}")

        fit_end = period_start
        periods.append(fitDates(fit_start, fit_end, period_start, period_end, no_data=False))

    if date_method in [ROLLING, EXPANDING] and len(boundaries) >= 2:
        periods = [
            fitDates(
                start_date,
                start_date,
                start_date,
                boundaries[1],
                no_data=True,
            )
        ] + periods

    return listOfFittingDates(periods)


def _list_of_starting_dates_per_period(
    start_date: datetime.datetime,
    end_date: datetime.datetime,
    interval_frequency: str = "12M",
):
    if interval_frequency == "W":
        use_interval_frequency = "7D"
    elif interval_frequency == "M":
        use_interval_frequency = "30D"
    elif interval_frequency in ["12M", "Y"]:
        use_interval_frequency = "365D"
    else:
        use_interval_frequency = interval_frequency

    results = list(pd.date_range(end_date, start_date, freq="-" + use_interval_frequency))
    results.reverse()
    return results
