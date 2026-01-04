# quantlib

Minimal, self-contained CLI tools and library for quantitative finance.

## Subcommands

- **[corr](src/correlation/README.md)**: Compute correlation matrices over time from returns.
- **[costs](src/src/costs/README.md)**: Calculate Sharpe Ratio (SR) costs for instruments based on spread and fees.

## Install (editable - for developers)

From the repo root:

- `cd quantlib`
- `python -m pip install -e .`

This installs the `quantlib` command.

## Build a single binary with PyInstaller

From `quantlib/`:

- `make build`

Binary will be at `dist/quantlib`.
