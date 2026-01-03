from __future__ import annotations

import datetime
from dataclasses import dataclass

import pandas as pd

from .fitting_dates import generate_fitting_dates, listOfFittingDates
from .exponential_correlation import (
    CorrelationEstimate,
    ExponentialCorrelationResults,
    create_boring_corr_matrix,
    modify_correlation,
)


@dataclass
class CorrelationList:
    corr_list: list[CorrelationEstimate]
    column_names: list[str]
    fit_dates: listOfFittingDates


def correlation_over_time_for_returns(
    returns_for_correlation: pd.DataFrame,
    frequency: str = "D",
    forward_fill_price_index: bool = True,
    **kwargs,
) -> CorrelationList:
    # Build a synthetic price index from returns, resample, then diff.
    # For daily frequency, this is essentially a no-op aside from losing the first row.
    index_prices_for_correlation = returns_for_correlation.cumsum()
    if forward_fill_price_index:
        index_prices_for_correlation = index_prices_for_correlation.ffill()

    index_prices_for_correlation = index_prices_for_correlation.resample(frequency).last()
    returns_for_correlation = index_prices_for_correlation.diff()

    return correlation_over_time(returns_for_correlation, **kwargs)


def correlation_over_time(
    data_for_correlation: pd.DataFrame,
    date_method: str = "in_sample",
    rollyears: int = 20,
    interval_frequency: str = "12M",
    using_exponent: bool = True,
    ew_lookback: int = 250,
    min_periods: int = 20,
    no_data_offdiag: float = 0.99,
    floor_at_zero: bool = True,
    clip: float | None = None,
    shrinkage: float = 0.0,
) -> CorrelationList:
    column_names = list(data_for_correlation.columns)

    fit_dates = generate_fitting_dates(
        data_for_correlation,
        date_method=date_method,
        rollyears=rollyears,
        interval_frequency=interval_frequency,
    )

    corr_list: list[CorrelationEstimate] = []

    if using_exponent:
        results = ExponentialCorrelationResults(
            data_for_correlation, ew_lookback=ew_lookback, min_periods=min_periods
        )

        for fit_period in fit_dates:
            if getattr(fit_period, "no_data", False):
                corr_list.append(
                    create_boring_corr_matrix(
                        len(column_names), column_names, offdiag=no_data_offdiag
                    )
                )
                continue

            corr = results.last_valid_cor_matrix_for_date(fit_period.fit_end)
            if pd.isna(corr.values).all():
                corr = create_boring_corr_matrix(
                    len(column_names), column_names, offdiag=no_data_offdiag
                )

            corr = modify_correlation(
                corr,
                floor_at_zero=floor_at_zero,
                clip_value=clip,
                shrinkage=shrinkage,
            )
            corr_list.append(corr)

    else:
        for fit_period in fit_dates:
            if getattr(fit_period, "no_data", False):
                corr_list.append(
                    create_boring_corr_matrix(
                        len(column_names), column_names, offdiag=no_data_offdiag
                    )
                )
                continue

            sub = data_for_correlation.loc[fit_period.fit_start : fit_period.fit_end]
            corr_pd = sub.corr()
            corr = CorrelationEstimate(values=corr_pd.values, columns=column_names)
            corr = modify_correlation(
                corr,
                floor_at_zero=floor_at_zero,
                clip_value=clip,
                shrinkage=shrinkage,
            )
            corr_list.append(corr)

    return CorrelationList(corr_list=corr_list, column_names=column_names, fit_dates=fit_dates)


def correlation_list_to_jsonable(corr_list: CorrelationList) -> dict:
    periods = []
    for fit_period, corr in zip(corr_list.fit_dates, corr_list.corr_list):
        periods.append(
            {
                "fit_start": _dt_to_iso(fit_period.fit_start),
                "fit_end": _dt_to_iso(fit_period.fit_end),
                "period_start": _dt_to_iso(fit_period.period_start),
                "period_end": _dt_to_iso(fit_period.period_end),
                "no_data": bool(getattr(fit_period, "no_data", False)),
                "correlation": corr.as_dict(),
            }
        )

    return {
        "columns": list(corr_list.column_names),
        "periods": periods,
    }


def _dt_to_iso(dt: datetime.datetime) -> str:
    if isinstance(dt, pd.Timestamp):
        dt = dt.to_pydatetime()
    if dt.tzinfo is not None:
        return dt.isoformat()
    return dt.replace(tzinfo=datetime.timezone.utc).isoformat()
