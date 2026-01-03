from __future__ import annotations

import datetime
from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class CorrelationEstimate:
    values: np.ndarray
    columns: list[str]

    def as_dict(self) -> dict:
        return {
            "columns": list(self.columns),
            "values": self.values.tolist(),
        }

    def floor_at_zero(self) -> "CorrelationEstimate":
        values = self.values.copy()
        values[values < 0.0] = 0.0
        np.fill_diagonal(values, 1.0)
        return CorrelationEstimate(values=values, columns=self.columns)

    def clip(self, clip_value: float | None) -> "CorrelationEstimate":
        if clip_value is None:
            return self
        clip_value = abs(float(clip_value))
        values = self.values.copy()
        values[values < -clip_value] = -clip_value
        values[values > clip_value] = clip_value
        np.fill_diagonal(values, 1.0)
        return CorrelationEstimate(values=values, columns=self.columns)

    def shrink_to_average(self, shrinkage: float) -> "CorrelationEstimate":
        shrinkage = float(shrinkage)
        if shrinkage <= 0.0:
            return self
        if shrinkage >= 1.0:
            shrinkage = 1.0

        values = self.values.copy()
        vals = values.copy()
        np.fill_diagonal(vals, np.nan)
        avg = np.nanmean(vals)
        if np.isnan(avg):
            return self

        prior = np.full_like(values, avg, dtype=float)
        np.fill_diagonal(prior, 1.0)
        shrunk = shrinkage * prior + (1.0 - shrinkage) * values
        np.fill_diagonal(shrunk, 1.0)
        return CorrelationEstimate(values=shrunk, columns=self.columns)


def modify_correlation(
    corr: CorrelationEstimate,
    *,
    floor_at_zero: bool = True,
    shrinkage: float = 0.0,
    clip_value: float | None = None,
) -> CorrelationEstimate:
    if floor_at_zero:
        corr = corr.floor_at_zero()
    corr = corr.clip(clip_value)
    if shrinkage and shrinkage > 0.0:
        corr = corr.shrink_to_average(shrinkage)
    return corr


def create_boring_corr_matrix(
    size: int, columns: list[str], offdiag: float = 0.99
) -> CorrelationEstimate:
    values = np.full((size, size), offdiag, dtype=float)
    np.fill_diagonal(values, 1.0)
    return CorrelationEstimate(values=values, columns=columns)


class ExponentialCorrelationResults:
    def __init__(
        self, data_for_correlation: pd.DataFrame, ew_lookback: int = 250, min_periods: int = 20
    ):
        self._columns = list(data_for_correlation.columns)
        self._raw_correlations = data_for_correlation.ewm(
            span=ew_lookback, min_periods=min_periods, ignore_na=True
        ).corr(pairwise=True)

    @property
    def raw_correlations(self) -> pd.DataFrame:
        return self._raw_correlations

    @property
    def columns(self) -> list[str]:
        return self._columns

    def last_valid_cor_matrix_for_date(self, date_point: datetime.datetime) -> CorrelationEstimate:
        return last_valid_cor_matrix_for_date(self.raw_correlations, self.columns, date_point)


def last_valid_cor_matrix_for_date(
    raw_correlations: pd.DataFrame, columns: list[str], date_point: datetime.datetime
) -> CorrelationEstimate:
    size_of_matrix = len(columns)
    subset = raw_correlations[raw_correlations.index.get_level_values(0) < date_point]

    if subset.shape[0] < size_of_matrix:
        return CorrelationEstimate(
            values=np.full((size_of_matrix, size_of_matrix), np.nan),
            columns=columns,
        )

    corr_matrix_values = subset.tail(size_of_matrix).values
    return CorrelationEstimate(values=corr_matrix_values, columns=columns)
