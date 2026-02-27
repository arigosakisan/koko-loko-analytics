"""CLI entry point for Koko Loko Analytics Suite."""

import argparse
import logging
import sys

from src.report import generate_weekly_report
from src.menu import analyze_menu
from src.social import generate_all_content


def setup_logging(verbose: bool = False) -> None:
    """Configure logging for the application.

    Args:
        verbose: If True, set log level to DEBUG; otherwise INFO.
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser.

    Returns:
        Configured ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        prog="koko-loko",
        description="Koko Loko Restaurant Analytics & Automation Suite",
    )
    parser.add_argument(
        "--input", "-i",
        default="data/sales_sample.csv",
        help="Path to sales data file (CSV or XLSX)",
    )
    parser.add_argument(
        "--output", "-o",
        default="output",
        help="Output directory for reports and charts (default: output)",
    )
    parser.add_argument(
        "--lang", "-l",
        choices=["en", "sr"],
        default="en",
        help="Output language: en (English) or sr (Serbian)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Report command
    report_parser = subparsers.add_parser("report", help="Generate weekly sales report")
    report_parser.add_argument(
        "--week-end",
        default=None,
        help="End date of the target week (YYYY-MM-DD). Defaults to latest date in data.",
    )

    # Menu command
    subparsers.add_parser("menu", help="Run menu performance analysis")

    # Social command
    subparsers.add_parser("social", help="Generate social media content")

    # All command
    subparsers.add_parser("all", help="Run all analyses")

    return parser


def main() -> None:
    """Main entry point for the CLI application."""
    parser = build_parser()
    args = parser.parse_args()
    setup_logging(args.verbose)

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    if args.command in ("report", "all"):
        print("\n>>> Generating Weekly Sales Report...\n")
        week_end = getattr(args, "week_end", None)
        generate_weekly_report(args.input, args.output, week_end, args.lang)

    if args.command in ("menu", "all"):
        print("\n>>> Running Menu Performance Analysis...\n")
        analyze_menu(args.input, args.output, args.lang)

    if args.command in ("social", "all"):
        print("\n>>> Generating Social Media Content...\n")
        generate_all_content(args.input, args.output, args.lang)

    print("\nDone!")


if __name__ == "__main__":
    main()
