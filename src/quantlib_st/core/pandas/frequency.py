import pandas as pd


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
