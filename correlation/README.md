# Correlation Calculation

This module computes correlation matrices over time from return series.

## Usage

Input CSV format: first column is a datetime index; remaining columns are returns.

```bash
cat returns.csv | quantlib corr > correlations.json
```

### Common Options

- `--frequency W`: Resamples to weekly before correlating (default: `D`).
- `--date-method expanding|rolling|in_sample`: Controls the lookback window.
- `--rollyears 20`: Used only when `--date-method rolling`.
- `--interval-frequency 12M`: Controls how often a new correlation matrix is emitted.
- `--ew-lookback 250` and `--min-periods 20`: Parameters for EWMA estimation.

### Post-processing

- `--floor-at-zero / --no-floor-at-zero` (default: floor at zero): Replaces negative correlations with 0.
- `--clip 0.9` (default: no clipping): Clamps off-diagonal values to $[-c, +c]$.
- `--shrinkage 0.2` (default: 0): Blends the estimate with an average correlation prior.
