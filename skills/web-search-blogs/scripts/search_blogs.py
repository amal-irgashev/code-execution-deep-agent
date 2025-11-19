#!/usr/bin/env python3
"""Search for blog posts and articles about a company using Tavily.

Optimized for finding engineering blogs, technical articles, and thought
leadership content. Uses broader time windows since blogs publish less
frequently than news.
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
        description="Search for company blog posts and articles using Tavily"
    )
    parser.add_argument(
        "company",
        help="Company name to search (e.g., 'Anthropic', 'LlamaIndex')",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Number of days to look back (default: 30, blogs less frequent)",
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

    # Blog-focused query
    # Why: Targets engineering blogs, technical articles, company blog domains
    # More specific than generic "blog" search
    query = f"{args.company} engineering blog technical deep dive architecture"

    # Domain whitelist for engineering/technical blogs
    # Company blog subdomains + technical blogging platforms
    company_slug = args.company.lower().replace(' ', '')
    include_domains = [
        # Company blog subdomains (common patterns)
        f"blog.{company_slug}.com", f"blog.{company_slug}.ai",
        f"engineering.{company_slug}.com", f"{company_slug}.com/blog",
        # Technical blogging platforms
        "medium.com", "dev.to", "substack.com",
        # General company domains (fallback)
        f"{company_slug}.com", f"{company_slug}.ai",
    ]

    # Execute search
    try:
        # Use "general" topic for blogs (more comprehensive than "news")
        # Include domains filters to target actual blog properties
        response = client.search(
            query=query,
            search_depth="advanced",
            topic="general",  # Better for blog content
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
        "search_type": "blogs",
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
                "search_type": "blogs",
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

