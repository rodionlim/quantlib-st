# pandl_calculators

P&L calculators turn _positions + prices (+ costs)_ into P&L series.

- `pandlCalculation` defines the base mechanics (price returns → P&L in points/currency).
- `pandlCalculationWithGenericCosts` adds cost layers (gross/net/costs curves).
- `pandlCalculationWithSRCosts` implements SR-style cost drag.

Think of a calculator as the _engine_ that produces a curve, while `accountCurve` is the
_presentation layer_ for that output.
