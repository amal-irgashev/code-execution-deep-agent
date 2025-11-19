#!/usr/bin/env python3
"""Search for documentation updates and API changes using Tavily.

Optimized for finding docs site updates, API reference changes, changelogs,
and release notes. Focuses on technical documentation domains.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    from tavily import TavilyClient
except ImportError:
    print(
        "Error: tavily-python not installed. Run: pip install tavily-python",
        file=sys.stderr,
    )
    sys.exit(1)


def main():
    """Parse CLI arguments and execute Tavily search."""
    parser = argparse.ArgumentParser(
        description="Search for documentation and API updates using Tavily"
    )
    parser.add_argument(
        "company",
        help="Company name to search (e.g., 'Anthropic', 'LlamaIndex')",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=14,
        help="Number of days to look back (default: 14)",
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=10,
        help="Maximum number of results to return (default: 10)",
    )
    parser.add_argument(
        "--output",
        help="Optional: Path to save JSON output file",
    )

    args = parser.parse_args()

    # Validate API key
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        print(
            "Error: TAVILY_API_KEY environment variable not set.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Initialize client
    try:
        client = TavilyClient(api_key=api_key)
    except Exception as e:
        print(f"Error: Failed to initialize Tavily client: {e}", file=sys.stderr)
        sys.exit(1)

    # Docs-focused query
    # Why: Targets documentation sites, API references, changelogs
    query = f"{args.company} API documentation changelog release notes updates"

    # Domain whitelist for documentation sites
    # Docs/API subdomains + developer portals
    company_slug = args.company.lower().replace(' ', '')
    include_domains = [
        # Documentation subdomains (common patterns)
        f"docs.{company_slug}.com", f"docs.{company_slug}.ai",
        f"api.{company_slug}.com", f"developer.{company_slug}.com",
        f"{company_slug}.com/docs", f"{company_slug}.com/api",
        # Platform docs (for cloud providers)
        "docs.aws.amazon.com", "cloud.google.com/docs",
        "learn.microsoft.com", "docs.github.com",
        # General company domains (fallback)
        f"{company_slug}.com", f"{company_slug}.ai",
    ]

    # Execute search
    try:
        # General topic for docs (docs sites often don't classify as "news")
        # Include domains targets docs/api subdomains specifically
        response = client.search(
            query=query,
            search_depth="advanced",
            topic="general",
            days=args.days,
            max_results=args.max_results,
            include_domains=include_domains,
        )
    except Exception as e:
        print(f"Error: Tavily search failed: {e}", file=sys.stderr)
        sys.exit(1)

    # Normalize response
    results = []
    for item in response.get("results", []):
        # Optionally filter/boost results from docs domains
        # (For MVP, we'll trust Tavily's ranking)
        results.append({
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "published_at": item.get("published_date"),
            "content": item.get("content", ""),
            "score": item.get("score", 0.0),
        })

    # Build output
    output_data = {
        "company": args.company,
        "search_type": "documentation",
        "queried_at": datetime.now(timezone.utc).isoformat(),
        "lookback_days": args.days,
        "results": results,
        "total_results": len(results),
    }

    # Write to file
    if args.output:
        try:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump(output_data, f, indent=2)
            
            # Print concise summary to stdout (token-efficient for agents)
            summary = {
                "saved_to": str(output_path),
                "company": args.company,
                "search_type": "documentation",
                "total_results": len(results),
                "top_result": results[0]["title"] if results else None,
                "lookback_days": args.days,
            }
            print(json.dumps(summary, indent=2))
        except Exception as e:
            print(f"Error: Failed to write output file: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()

