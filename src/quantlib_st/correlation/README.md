# Correlation Calculation

This module computes correlation matrices over time from data series.

## Usage

Input CSV format: first column is a datetime index; remaining columns are values to compute correlationagainst.

```bash
cat sample_data/returns_10x4.csv | quantlib corr > correlations.json
cat sample_data/returns_10x4.csv | ./dist/quantlib corr
```

### Common Options

- `--frequency W`: Resamples to weekly before correlating (default: `D`).
- `--date-method expanding|rolling|in_sample`: Controls the lookback window.
- `--rollyears 20`: Used only when `--date-method rolling`.
- `--interval-frequency 12M`: Controls how often a new correlation matrix is emitted.
- `--ew-lookback 250` and `--min-periods 20`: Parameters for EWMA estimation.
- `--is-price-series`: Treat input data as price series and convert to lognormal returns.

### Key concepts

- `in_sample`: each correlation uses all the data you passed in.
- `expanding`: the estimation window grows over time — each new estimate keeps earlier data and adds newer data.
- `rolling`: use a fixed-size window that moves forward — old data drops out as the window advances.
- `generate_fitting_dates`: builds the list of date ranges (start/end) the code will use to compute each correlation matrix.
- `interval_frequency`: how often a new correlation matrix is reported (examples: `1M` = monthly, `3M` = quarterly, `12M` = yearly).
- `default correlation method`: computes the exponential weighted moving average of values before calculating correlations

The section below gives more technical details.

### Fitting dates and interval_frequency

The code uses a helper called `generate_fitting_dates` to produce a sequence of fitting periods. Each fitting period includes:

- `fit_start` / `fit_end`: the date range used to compute the correlation estimate.
- `period_start` / `period_end`: the date range for which that estimate applies (the emission window).
- `no_data`: a flag set when insufficient data is available for the period.

`interval_frequency` controls how often a new correlation matrix is emitted (for example `1M`, `3M`, `12M`). The generator yields fitting periods spaced by `interval_frequency`; for each period the library computes (or substitutes) a correlation matrix which is then reported for that emission window.

`generate_fitting_dates` therefore decouples the choice of lookback window (controlled by `--date-method` and `--rollyears`) from the cadence of outputs (`--interval-frequency`), and is used by `correlation_over_time` to iterate over periods and build the ordered list of correlation matrices.

### Post-processing

- `--floor-at-zero / --no-floor-at-zero` (default: floor at zero): Replaces negative correlations with 0.
- `--clip 0.9` (default: no clipping): Clamps off-diagonal values to $[-c, +c]$.
- `--shrinkage 0.2` (default: 0): Blends the estimate with an average correlation prior.
