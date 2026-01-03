# quantlib

Minimal, self-contained CLI tools.

`corr` is the first command implemented; more subcommands can be added later.

## Install (editable)

From the repo root:

- `cd quantlib`
- `python -m pip install -e .`

This installs the `quantlib` command.

## Usage

Input CSV format: first column is a datetime index; remaining columns are returns.

- `cat returns.csv | quantlib corr > correlations.json`

Sample data for sanity checking is in [quantlib/sample_data/returns_10x4.csv](quantlib/sample_data/returns_10x4.csv).
This command should produce correlations that are not all 0.99/1.0:

- `cat sample_data/returns_10x4.csv | quantlib corr --frequency D --date-method in_sample --ew-lookback 5 --min-periods 3 --no-floor-at-zero`

Common options:

- `--frequency W` resamples to weekly before correlating
- `--date-method expanding|rolling|in_sample`
- `--rollyears 20` (used only when `--date-method rolling`)
- `--interval-frequency 12M` controls how often a new correlation matrix is emitted
- `--ew-lookback 250` and `--min-periods 20` for EWMA

Correlation post-processing:

- `--floor-at-zero/--no-floor-at-zero` (default: floor at zero)

  - Layman: negative correlations are replaced with 0.
  - Why: some systematic portfolio methods assume correlations are non-negative (or you want a conservative "don’t rely on negative correlation" stance).

- `--clip 0.9` (default: no clipping)

  - Layman: puts a "speed limit" on correlations so they can’t be too extreme.
  - What it does: clamps each off-diagonal value to the range $[-c, +c]$ where $c$ is your clip value.
  - When it helps: noisy/small-sample estimates that jump to very high (or very low) correlations.

- `--shrinkage 0.2` (default: 0)
  - Layman: blends your estimated correlation matrix with a more boring/average one.
  - What it does: $C_{shrunk} = \lambda C_{prior} + (1-\lambda)C_{est}$ where $\lambda$ is shrinkage.
  - In this CLI, the "prior" uses the average off-diagonal correlation (diag stays 1). Higher shrinkage = more conservative/stable.

## Build a single binary with PyInstaller

From `quantlib/`:

- `python -m pip install pyinstaller`
- `pyinstaller --onefile --paths . -n quantlib quantlib_launcher.py`

Binary will be at `dist/quantlib`.
