from __future__ import annotations

import argparse
import json
import sys
from io import StringIO


def add_costs_subcommand(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "costs",
        help="Calculate SR costs for an instrument from price CSV piped on stdin or provided via file.",
    )

    parser.add_argument(
        "--instrument",
        required=True,
        help="Instrument code (e.g., ES, GC).",
    )
    parser.add_argument(
        "--config",
        help="Path to JSON file containing instrument cost configuration.",
    )
    parser.add_argument(
        "--use-ibkr",
        action="store_true",
        help="Use IBKR API for cost data (currently a stub).",
    )
    parser.add_argument(
        "--vol",
        type=float,
        help="Override annualized volatility (as a decimal, e.g., 0.15 for 15%%).",
    )
    parser.add_argument(
        "--price",
        type=float,
        help="Override current price (otherwise uses the last price in the CSV).",
    )

    parser.set_defaults(_handler=handle_costs)


def handle_costs(args: argparse.Namespace) -> int:
    import pandas as pd
    from quantlib_st.costs.data_source import ConfigFileCostDataSource, IBKRCostDataSource
    from quantlib_st.costs.calculator import (
        calculate_sr_cost,
        calculate_annualized_volatility,
        calculate_recent_average_price,
        calculate_cost_percentage_terms,
    )

    # 1. Get Cost Config
    if args.use_ibkr:
        data_source = IBKRCostDataSource()
    elif args.config:
        data_source = ConfigFileCostDataSource(args.config)
    else:
        print("Error: Must provide either --config or --use-ibkr", file=sys.stderr)
        return 1

    try:
        cost_config = data_source.get_cost_config(args.instrument)
    except Exception as e:
        print(f"Error fetching cost config: {e}", file=sys.stderr)
        return 1

    # 2. Get Price Data
    if not sys.stdin.isatty():
        # Read from stdin
        input_data = sys.stdin.read()
        df = pd.read_csv(StringIO(input_data), index_col=0, parse_dates=True)
    else:
        # If no stdin, we need at least --price and --vol if we want to calculate anything
        df = pd.DataFrame()

    if df.empty and (args.price is None or args.vol is None):
        print(
            "Error: Must pipe price CSV to stdin or provide both --price and --vol overrides.",
            file=sys.stderr,
        )
        return 1

    # 3. Determine Price and Volatility
    if args.price is not None:
        average_price = float(args.price)
    else:
        # Use average price over the last year (256 days)
        average_price = calculate_recent_average_price(df.iloc[:, 0])

    if args.vol is not None:
        # If user provides --vol, we assume it's annualized volatility in price units
        ann_stdev_price_units = float(args.vol)
    else:
        # Calculate annualized volatility in price units (average over last year)
        ann_stdev_price_units = float(calculate_annualized_volatility(df.iloc[:, 0]))

    # 4. Calculate Costs
    sr_cost = float(
        calculate_sr_cost(
            cost_config,
            price=average_price,
            ann_stdev_price_units=ann_stdev_price_units,
        )
    )

    pct_cost = float(
        calculate_cost_percentage_terms(
            cost_config,
            blocks_traded=1.0,
            price=average_price,
        )
    )

    # 5. Output Results
    result = {
        "instrument": args.instrument,
        "average_price": round(average_price, 4),
        "ann_stdev_price_units": round(ann_stdev_price_units, 4),
        "sr_cost": round(sr_cost, 5),
        "percentage_cost": round(pct_cost, 6),
    }

    print(json.dumps(result, indent=2))
    return 0
