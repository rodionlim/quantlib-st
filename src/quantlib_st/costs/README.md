# Costs Calculation

This module calculates the **Sharpe Ratio (SR) Cost** of trading an instrument, following the methodology used in `pysystemtrade`.

## How it works

The SR Cost represents the expected reduction in a strategy's Sharpe Ratio due to trading costs (spread and commissions). It is calculated as:

$$SR_{cost} = \frac{\text{Annualized Cost}}{\text{Annualized Volatility}}$$

### 1. Annualized Cost

The cost of a single trade is the sum of:

- **Slippage**: Half the bid-ask spread multiplied by the point size.
- **Commission**: The maximum of per-trade, per-block, or percentage-based fees.

To annualize this, we assume a certain turnover (defaulting to 1 block traded for this CLI tool's estimation).

### 2. Annualized Volatility

Volatility is calculated using a robust method:

1. Calculate daily price changes (not percentage returns).
2. Apply an Exponentially Weighted Moving Average (EWMA) with a span of 35 days to the standard deviation of these changes.
3. Take the average of this daily volatility over the last year (256 business days).
4. Annualize by multiplying by $\sqrt{256}$.

### 3. Average Price

Costs are calculated using the average price over the last year (256 business days). This ensures the cost estimate is representative of the entire period and serves three purposes:

- **Percentage Commissions**: For instruments with percentage-based fees, the cost depends on the contract value ($\text{Price} \times \text{Point Size}$).
- **Stability**: It prevents temporary price spikes or crashes from distorting long-term cost expectations.
- **Consistency**: It matches the 256-day window used for the volatility calculation in the SR Cost denominator.

## Usage

```bash
cat prices.csv | quantlib costs --instrument ES --config instrument_costs.json
```

### Configuration (`instrument_costs.json`)

```json
{
  "instrument_code": "ES",
  "point_size": 50,
  "price_slippage": 0.125,
  "per_trade_commission": 2.05
}
```
