from __future__ import annotations

import datetime
import numpy as np
import pandas as pd

from dataclasses import dataclass
from typing import Literal

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

    def as_(
        self, fmt: Literal["jsonable", "long", "original"] = "jsonable"
    ) -> dict | list[dict] | CorrelationList:
        """Return the correlation list in a requested format.

        Parameters
        ----------
        fmt : str
            One of:
            - "jsonable" (default) -> returns the JSON-serializable dict produced
              by :func:`correlation_list_to_jsonable`.
            - "long" -> returns a list of tidy records (dicts) produced by
              :func:`jsonable_to_long` (uses the jsonable form internally).
            - "original" -> returns the original :class:`CorrelationList` object.

        Rationale
        ---------
        - A single accessor on the data structure makes it easy for callers to
          request the representation they need (API response, UI-friendly long
          table, or raw object for further processing).
        - The method delegates to existing helpers to avoid duplicate logic and
          ensures consistent serialization/conversion.
        """
        key = fmt.lower()
        if key in ("jsonable", "json", "dict"):
            return correlation_list_to_jsonable(self)
        if key in ("long", "long_format", "records"):
            return jsonable_to_long(correlation_list_to_jsonable(self))
        if key in ("original", "self"):
            return self
        raise ValueError(f"Unknown format: {fmt}")


def correlation_over_time(
    data_for_correlation: pd.DataFrame,
    frequency: str = "D",
    forward_fill_price_index: bool = True,
    is_price_series: bool = False,
    **kwargs,
) -> CorrelationList:
    """Construct a CorrelationList from a DataFrame of returns or prices.

    This helper builds a (log) price index, optionally forward-filling missing
    values, resampling at the requested ``frequency``, and converting back to
    returns (diff) before delegating to :func:`compute_correlation_over_time`.

    Input Requirement
    -----------------
    - If ``is_price_series=True``, input is expected to be a raw Price series.
      It will be converted to log-prices internally so that resampling and
      differencing yields log-normal returns.
    - If ``is_price_series=False``, input is expected to be log-normal returns.

    Parameters
    ----------
    data_for_correlation : pd.DataFrame
        Input data; rows should be indexed by a datetime-like index.
    frequency : str, optional
        Resampling frequency passed to ``DataFrame.resample`` (default: "D").
    forward_fill_price_index : bool, optional
        Forward-fill the price index prior to resampling (default: True).
    is_price_series : bool, optional
        If True, treat input as a price index and log-transform it. If False
        (default), treat input as log-normal returns.
    **kwargs :
        All other keyword arguments are forwarded to :func:`compute_correlation_over_time`.
    """
    # 1. Determine the (log) Price Index
    if is_price_series:
        # Input is Price P; we want ln(P) so that diff() yields log-returns.
        index_prices_for_correlation = pd.DataFrame(
            np.log(data_for_correlation),
            index=data_for_correlation.index,
            columns=data_for_correlation.columns,
        )
    else:
        # Input is log-normal returns; cumsum yields the log-price index.
        index_prices_for_correlation = data_for_correlation.cumsum()

    # 2. Forward fill if requested
    if forward_fill_price_index:
        index_prices_for_correlation = index_prices_for_correlation.ffill()

    # 3. Resample and diff to get log-normal returns
    index_prices_for_correlation = index_prices_for_correlation.resample(
        frequency
    ).last()
    returns_for_correlation = index_prices_for_correlation.diff()

    return compute_correlation_over_time(returns_for_correlation, **kwargs)


def correlation_over_time_for_price(
    data_for_correlation: pd.DataFrame, **kwargs
) -> CorrelationList:
    """Wrapper for correlation_over_time when input is a price series."""
    return correlation_over_time(data_for_correlation, is_price_series=True, **kwargs)


def correlation_over_time_for_returns(
    data_for_correlation: pd.DataFrame, **kwargs
) -> CorrelationList:
    """Wrapper for correlation_over_time when input is a returns series."""
    return correlation_over_time(data_for_correlation, is_price_series=False, **kwargs)


def compute_correlation_over_time(
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

    return CorrelationList(
        corr_list=corr_list, column_names=column_names, fit_dates=fit_dates
    )


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


def jsonable_to_long(jsonable: dict) -> list[dict]:
    """Convert correlation-list jsonable -> long records.

    Rationale:
    - Long (tidy) format of (date, pair, value, metadata) is easy to consume in UIs
      for line charts, data grids, and CSV export. It avoids nested matrices and
      simplifies filtering/aggregation on the client side.
    - This helper uses the *fit_end* as the canonical timestamp for each period
      (this makes the point represent the end of the fitting window); change if
      you prefer *period_start* or *fit_start* instead.
    - Converts missing/NaN values to ``None`` so JSON serialization yields
      ``null`` which is convenient for JavaScript charting libraries.

    Returns
    -------
    list[dict]
        Rows with keys: ``date``, ``pair``, ``value``, ``fit_start``, ``fit_end``,
        ``period_start``, ``period_end``, ``no_data``.
    """
    rows: list[dict] = []
    cols = jsonable["columns"]
    for p in jsonable["periods"]:
        date = p["fit_end"]
        meta = {
            "fit_start": p["fit_start"],
            "fit_end": p["fit_end"],
            "period_start": p["period_start"],
            "period_end": p["period_end"],
            "no_data": p.get("no_data", False),
        }
        mat = p["correlation"]["values"]
        for i, a in enumerate(cols):
            for j, b in enumerate(cols):
                if j <= i:
                    continue
                val = mat[i][j]
                val = None if pd.isna(val) else val
                rows.append({"date": date, "pair": f"{a}__{b}", "value": val, **meta})
    return rows


def _dt_to_iso(dt: datetime.datetime) -> str:
    if isinstance(dt, pd.Timestamp):
        dt = dt.to_pydatetime()
    if dt.tzinfo is not None:
        return dt.isoformat()
    return dt.replace(tzinfo=datetime.timezone.utc).isoformat()
