from __future__ import annotations

import argparse
import json
import sys
from io import StringIO


def add_corr_subcommand(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "corr",
        help="Compute correlations over time from CSV piped on stdin (outputs JSON).",
    )

    parser.add_argument(
        "--frequency",
        default="D",
        help="Resample frequency before correlation (default: D). Use W if you want weekly.",
    )
    parser.add_argument(
        "--date-method",
        default="in_sample",
        choices=["expanding", "rolling", "in_sample"],
        help="How to choose the fit window over time (default: in_sample)",
    )
    parser.add_argument(
        "--rollyears",
        type=int,
        default=20,
        help="Rolling years (used only if --date-method rolling; default: 20)",
    )
    parser.add_argument(
        "--interval-frequency",
        default="12M",
        help="How often to emit a new correlation matrix (default: 12M)",
    )

    parser.add_argument(
        "--using-exponent",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Use EWMA correlation (default: true)",
    )
    parser.add_argument(
        "--ew-lookback",
        type=int,
        default=250,
        help="EWMA span/lookback (default: 250)",
    )
    parser.add_argument(
        "--min-periods",
        type=int,
        default=20,
        help="Minimum observations before correlations appear (default: 20)",
    )

    parser.add_argument(
        "--floor-at-zero",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Floor negative correlations at 0 (default: true)",
    )
    parser.add_argument(
        "--clip",
        type=float,
        default=None,
        help="Optional absolute clip value for correlations (e.g. 0.9)",
    )
    parser.add_argument(
        "--shrinkage",
        type=float,
        default=0.0,
        help="Optional shrinkage-to-average in [0,1] (default: 0)",
    )

    parser.add_argument(
        "--forward-fill-price-index",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Forward fill the synthetic price index before resampling (default: true)",
    )
    parser.add_argument(
        "--is-price-series",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="If true, treat input as prices. If false (default), treat as returns.",
    )

    parser.add_argument(
        "--index-col",
        type=int,
        default=0,
        help="Which CSV column is the datetime index (default: 0)",
    )

    parser.set_defaults(_handler=run_corr)


def run_corr(args: argparse.Namespace) -> int:
    import pandas as pd
    from quantlib_st.correlation.correlation_over_time import (
        correlation_over_time,
        correlation_list_to_jsonable,
    )

    csv_text = sys.stdin.read()
    if not csv_text.strip():
        print(json.dumps({"error": "no input on stdin"}), file=sys.stderr)
        return 2

    try:
        df = pd.read_csv(StringIO(csv_text), index_col=args.index_col, parse_dates=True)
    except Exception as e:
        print(json.dumps({"error": f"failed to parse CSV: {e}"}), file=sys.stderr)
        return 2

    df = df.sort_index()

    corr_list = correlation_over_time(
        df,
        frequency=args.frequency,
        forward_fill_price_index=args.forward_fill_price_index,
        is_price_series=args.is_price_series,
        date_method=args.date_method,
        rollyears=args.rollyears,
        interval_frequency=args.interval_frequency,
        using_exponent=args.using_exponent,
        ew_lookback=args.ew_lookback,
        min_periods=args.min_periods,
        floor_at_zero=args.floor_at_zero,
        clip=args.clip,
        shrinkage=args.shrinkage,
    )

    out = correlation_list_to_jsonable(corr_list)
    sys.stdout.write(json.dumps(out))
    sys.stdout.write("\n")
    return 0
