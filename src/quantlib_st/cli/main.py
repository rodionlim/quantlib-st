from __future__ import annotations

import argparse
import importlib.metadata

from quantlib_st.cli.corr_cmd import add_corr_subcommand
from quantlib_st.cli.costs_cmd import add_costs_subcommand


def get_version() -> str:
    """Get the version of quantlib-st package."""
    try:
        return importlib.metadata.version("quantlib-st")
    except importlib.metadata.PackageNotFoundError:
        return "unknown"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="quantlib",
        description="quantlib CLI (corr is the first subcommand; more will be added).",
    )

    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"%(prog)s {get_version()}",
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
