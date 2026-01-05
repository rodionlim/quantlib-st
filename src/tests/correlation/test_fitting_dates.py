import pandas as pd

from quantlib_st.correlation.fitting_dates import (
    generate_fitting_dates,
    IN_SAMPLE,
    EXPANDING,
    ROLLING,
)


def _make_df(start: str, end: str, freq: str = "ME") -> pd.DataFrame:
    idx = pd.date_range(start, end, freq=freq)
    return pd.DataFrame(index=idx, data={"x": 0})


def test_in_sample_returns_single_period():
    df = _make_df("2020-01-01", "2022-12-31")
    periods = generate_fitting_dates(df, date_method=IN_SAMPLE)

    assert len(periods) == 1
    p = periods[0]
    assert p.fit_start == df.index[0]
    assert p.fit_end == df.index[-1]
    assert p.period_start == df.index[0]
    assert p.period_end == df.index[-1]
    assert p.no_data is False


def test_expanding_uses_initial_start_for_estimation():
    df = _make_df("2018-01-01", "2022-12-31")
    periods = generate_fitting_dates(
        df, date_method=EXPANDING, interval_frequency="12M"
    )

    # There should be at least one real (non-no-data) period
    non_empty = [p for p in periods if not p.no_data]
    assert len(non_empty) >= 1

    # For expanding, all real periods should use the original start as fit_start
    assert all(p.fit_start == df.index[0] for p in non_empty)


def test_rolling_moves_fit_start_forward():
    df = _make_df("2018-01-01", "2022-12-31")
    # use a small rollyears so the fit_start should advance away from the original start
    periods = generate_fitting_dates(
        df, date_method=ROLLING, rollyears=1, interval_frequency="12M"
    )

    non_empty = [p for p in periods if not p.no_data]
    assert len(non_empty) >= 2

    # At least one period should have a fit_start later than the original data start
    assert any(p.fit_start > df.index[0] for p in non_empty)
