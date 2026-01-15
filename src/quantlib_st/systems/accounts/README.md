# Accounts and P&L Calculation

This directory contains the logic for converting trading signals (forecasts) into financial performance metrics (P&L curves).

## Mental Model: Converting Forecasts to P&L

The core function `pandl_for_instrument_forecast` follows a three-step process to determine the P&L of a strategy:

### 1. Risk-Based Baseline (`average_notional_position`)

Before looking at the actual signal strength, we calculate a "baseline" position size. This is the amount of the instrument we would hold if we had a standard-strength signal (a forecast of 10).

- **Goal**: To ensure that the strategy's risk is constant over time, regardless of market volatility.
- **Mechanism**: We divide a cash volatility target (derived from `capital` and `risk_target`) by the instrument's daily price volatility.
- **Result**: When volatility is high, the baseline position is small; when volatility is low, the baseline position is large.

### 2. Forecast Normalization (`normalised_forecast`)

In this framework, a "standard strength" signal is defined as a forecast of **10**.

- **The Division**: We divide the raw `forecast` by `target_abs_forecast` (default 10).
- **Why?**: This transforms the forecast into a **multiplier** (unitless).
  - A forecast of `10` becomes `1.0` (standard).
  - A forecast of `20` becomes `2.0` (twice the commitment).
  - A forecast of `0` becomes `0.0` (no position).
- **Benefit**: It separates the _conviction_ of the signal from the _risk management_ of the position sizing.

### 3. Final Position Sizing (`aligned_average * normalised_forecast`)

The actual amount we trade is the product of the two previous steps.

- **Mental Model**: `Actual Position = (Risk-Adjusted Baseline) * (Signal Strength Multiplier)`.
- **Meaning**: We take our "standard risk" size and scale it up or down based on how strong our forecast is relative to the "standard" 10.

## Directory Structure

- **[account_forecast.py](account_forecast.py)**: The high-level API. Orchestrates the normalization and sizing logic to produce an `accountCurve`.
- **[curves/](curves/)**: The **Presentation Layer**. Contains the `accountCurve` class, which subclasses `pd.Series` to provide performance statistics like Sharpe Ratio, Drawdowns, and Sortino.
- **[pandl_calculators/](pandl_calculators/)**: The **Engine Room**. Contains modular calculators that take positions and prices to compute Gross P&L, Costs, and Net P&L.

## Usage Flow

1. **Input**: A `forecast` series and a `price` series.
2. **Process**:
   - Calculate volatility using `estimators/vol`.
   - Scale the forecast to a multiplier.
   - Calculate the vol-weighted notional position.
   - Pass these to a `pandlCalculator`.
3. **Output**: An `accountCurve` object ready for analysis.

## Usage Example

```python
import pandas as pd

from quantlib_st.core.algos.forecast import DefaultForecastAlgo
from quantlib_st.systems.accounts.account_forecast import pandl_for_instrument_forecast
# Sample price data
price = pd.Series(
    [100, 101, 102, 101, 103, 104, 105, 109, 105, 107, 108, 110, 111, 115],
    index=pd.date_range(start='2023-01-01', periods=14, freq='D')
)
# Sample forecast data
ewmac = DefaultForecastAlgo.calc_ewmac_forecast(price, 4)

# Generate P&L curve
account = pandl_for_instrument_forecast(
    forecast=ewmac,
    price=price,
)
print(account.curve())
```
