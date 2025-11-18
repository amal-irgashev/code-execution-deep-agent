#!/usr/bin/env python3
"""Filter CSV rows by numeric column value and return top results.

This script efficiently filters large CSV files without loading them into
the LLM context. It outputs JSON for easy parsing by the agent.
"""

import argparse
import json
import sys
from pathlib import Path

import pandas as pd


def main():
    """Parse arguments and filter CSV data."""
    parser = argparse.ArgumentParser(
        description="Filter CSV by numeric column and return top N results"
    )
    parser.add_argument("csv_path", help="Path to CSV file")
    parser.add_argument("column_name", help="Column name to filter and sort by")
    parser.add_argument(
        "threshold",
        type=float,
        default=0,
        nargs="?",
        help="Minimum value threshold (default: 0)",
    )
    parser.add_argument(
        "--top", type=int, default=10, help="Number of top results to return (default: 10)"
    )

    args = parser.parse_args()

    # Validate file exists
    csv_path = Path(args.csv_path)
    if not csv_path.exists():
        print(f"Error: File not found: {args.csv_path}", file=sys.stderr)
        sys.exit(1)

    try:
        # Read CSV
        df = pd.read_csv(csv_path)

        # Validate column exists
        if args.column_name not in df.columns:
            print(
                f"Error: Column '{args.column_name}' not found. "
                f"Available columns: {', '.join(df.columns)}",
                file=sys.stderr,
            )
            sys.exit(1)

        # Filter by threshold
        filtered = df[df[args.column_name] >= args.threshold]

        # Sort descending and take top N
        top_results = filtered.nlargest(args.top, args.column_name)

        # Convert to JSON
        result = top_results.to_dict(orient="records")

        # Output JSON to stdout
        print(json.dumps(result, indent=2, default=str))

    except pd.errors.EmptyDataError:
        print(f"Error: CSV file is empty: {args.csv_path}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error processing CSV: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

