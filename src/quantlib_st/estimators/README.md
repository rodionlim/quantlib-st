# estimators

Small, focused volatility estimators.

- **robust_vol_calc** — Robust exponential volatility estimator for daily returns. Uses EWM std with an absolute minimum and an optional volatility floor.

- **mixed_vol_calc** — Blends short-term (robust) vol with a long-term slow vol component.

Usage example

```python
from quantlib_st.estimators.vol import robust_vol_calc
vol = robust_vol_calc(returns_series)
```

Notes

- If you have price data, use `robust_daily_vol_given_price(price_series)` which resamples to business days
  (taking the last price per business day) and computes differences to produce daily returns.
