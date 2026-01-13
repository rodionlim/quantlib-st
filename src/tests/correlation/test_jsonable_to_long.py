import pandas as pd
import numpy as np

from quantlib_st.correlation.correlation_over_time import (
    correlation_over_time,
    correlation_list_to_jsonable,
    jsonable_to_long,
)


def test_jsonable_to_long_expanding_multiple_periods():
    # 100 daily observations for 3 assets
    data = pd.DataFrame(
        np.random.RandomState(0).randn(100, 3),
        columns=["A", "B", "C"],
        index=pd.date_range(start="2020-01-01", periods=100, freq="D"),
    )

    cl = correlation_over_time(
        data,
        frequency="D",
        date_method="expanding",
        interval_frequency="7D",
        ew_lookback=50,
        min_periods=5,
    )

    j = correlation_list_to_jsonable(cl)
    rows = jsonable_to_long(j)

    assert isinstance(rows, list)
    assert len(rows) > 0

    pairs = {r["pair"] for r in rows}
    assert pairs == {"A__B", "A__C", "B__C"}

    sample = rows[0]
    for k in (
        "date",
        "pair",
        "value",
        "fit_start",
        "fit_end",
        "period_start",
        "period_end",
        "no_data",
    ):
        assert k in sample
