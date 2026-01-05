from __future__ import annotations

import argparse

from quantlib_st.cli.corr_cmd import add_corr_subcommand
from quantlib_st.cli.costs_cmd import add_costs_subcommand


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="quantlib",
        description="quantlib CLI (corr is the first subcommand; more will be added).",
    )

    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    add_corr_subcommand(subparsers)
    add_costs_subcommand(subparsers)

    args = parser.parse_args(argv)

    # Dispatch
    if args.subcommand == "corr":
        return args._handler(args)
    elif args.subcommand == "costs":
        return args._handler(args)

    parser.error(f"Unknown subcommand: {args.subcommand}")
    return 2
