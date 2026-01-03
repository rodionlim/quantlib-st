# quantlib

Minimal, self-contained CLI tools for quantitative finance.

## Subcommands

- **[corr](correlation/README.md)**: Compute correlation matrices over time from returns.
- **[costs](costs/README.md)**: Calculate Sharpe Ratio (SR) costs for instruments based on spread and fees.

## Install (editable)

From the repo root:

- `cd quantlib`
- `python -m pip install install -e .`

This installs the `quantlib` command.

## Build a single binary with PyInstaller

From `quantlib/`:

- `python -m pip install pyinstaller`
- `pyinstaller --onefile --paths . -n quantlib quantlib_launcher.py`

Binary will be at `dist/quantlib`.
