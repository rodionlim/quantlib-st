import pandas as pd
import numpy as np
import pytest

from quantlib_st.correlation.correlation_over_time import (
    correlation_over_time,
)


def test_correlationlist_as_variants():
    data = pd.DataFrame(
        np.random.RandomState(1).randn(100, 3),
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

    # jsonable form
    j = cl.as_("jsonable")
    assert isinstance(j, dict)
    assert "columns" in j and "periods" in j

    # long form
    rows = cl.as_("long")
    assert isinstance(rows, list)
    assert len(rows) > 0
    assert {r["pair"] for r in rows} == {"A__B", "A__C", "B__C"}

    # original
    o = cl.as_("original")
    assert o is cl

    # unknown
    with pytest.raises(ValueError):
        cl.as_("unsupported-form")  # type: ignore
