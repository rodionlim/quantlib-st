# curves

`accountCurve` is a lightweight wrapper around a P&L time series. It provides:

- consistent views (gross/net/costs, daily/weekly/monthly/annual),
- convenience stats (vol, sharpe, drawdown, etc.),
- a simple container for plotting and reporting.

Think of a curve as the _output_ of a P&L calculator: a standardized time series with
useful performance utilities attached.
