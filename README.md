# quantlib

[![PyPI version](https://badge.fury.io/py/quantlib-st.svg)](https://badge.fury.io/py/quantlib-st)
[![CI](https://github.com/rodionlim/quantlib-st/actions/workflows/ci.yml/badge.svg)](https://github.com/rodionlim/quantlib-st/actions/workflows/ci.yml)
[![GHCR](https://img.shields.io/badge/ghcr-quantlib--st-blue?logo=github)](https://github.com/rodionlim/quantlib-st/pkgs/container/quantlib-st)

Minimal, self-contained CLI tools and library for quantitative finance.

## Subcommands

- **[corr](src/quantlib_st/correlation/README.md)**: Compute correlation matrices over time from returns.
- **[costs](src/quantlib_st/costs/README.md)**: Calculate Sharpe Ratio (SR) costs for instruments based on spread and fees.

## Install (editable - for developers)

From the repo root:

- `cd quantlib`
- `python -m pip install -e .`

This installs the `quantlib` command.

## Docker

Pull a published image from GitHub Container Registry:

- `docker pull ghcr.io/rodionlim/quantlib-st:latest`

Run a quick correlation query by piping a CSV into the container (one-liner):

- `cat sample_data/returns_10x4.csv | docker run --rm -i ghcr.io/rodionlim/quantlib-st:latest corr --min-periods 3 --ew-lookback 10`

When publishing the image the Makefile also tags and pushes `:latest` in addition to the versioned tag.

## Package Sample Usage

```python
import pandas as pd
import numpy as np

from quantlib_st import correlation

# Sample data
data = pd.DataFrame(
    np.random.randn(100, 3),
    columns=['Asset_A', 'Asset_B', 'Asset_C'],
    index=pd.date_range(start='2020-01-01', periods=100, freq='D')  # daily dates
)
# Compute correlation matrix
corr_matrix = correlation.correlation_over_time(
    data,
    is_price_series=False,
    frequency='D', # resampling purpose
    interval_frequency='7D',
    date_method='expanding',
    ew_lookback=50,
    min_periods=10
)
print(corr_matrix.as_("jsonable"))
print(corr_matrix.as_("long"))
```
