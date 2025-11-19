#!/usr/bin/env python3
"""Search for recent web content about a company using Tavily.

This script provides a deterministic, opinionated interface to Tavily's search API
specifically optimized for competitive intelligence research. It focuses on:
- Recent news and announcements (configurable time window)
- High-quality sources (advanced search depth)
- Structured JSON output (easy parsing by agents)

Contract:
- Input: Company name + optional time window + max results
- Output: JSON with company name, timestamp, and search results array
- Errors: Clear messages to stderr + non-zero exit codes
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
        description="Search for recent company news/updates using Tavily"
    )
    parser.add_argument(
        "company",
        help="Company name to search (e.g., 'Anthropic', 'LlamaIndex')",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Number of days to look back (default: 7)",
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

    # Validate API key exists
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        print(
            "Error: TAVILY_API_KEY environment variable not set.\n"
            "Set it in your .env file or export it in your shell.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Initialize Tavily client
    try:
        client = TavilyClient(api_key=api_key)
    except Exception as e:
        print(f"Error: Failed to initialize Tavily client: {e}", file=sys.stderr)
        sys.exit(1)

    # Construct news-focused search query
    # Why this pattern: Optimized for breaking news and official announcements
    # - "press release" and "announces" capture official communications
    # - "launch" and "partnership" catch major business developments
    # - Company name ensures relevance
    query = f"{args.company} press release announces launch partnership news"

    # Domain whitelist for high-signal news sources
    # Company domains + major tech news outlets
    include_domains = [
        # Tech news outlets
        "techcrunch.com", "theverge.com", "cnbc.com", "axios.com",
        "bloomberg.com", "reuters.com", "venturebeat.com",
        # Company-specific (add dynamically if needed)
        f"{args.company.lower().replace(' ', '')}.com",
        f"{args.company.lower().replace(' ', '')}.ai",
    ]

    # Execute Tavily search with fixed parameters optimized for CI
    try:
        # Why these parameters:
        # - topic="news": Prioritizes recent, time-sensitive content
        # - search_depth="advanced": Higher quality, more relevant results
        # - days=N: Enforces recency constraint (Tavily filters by publish date)
        # - include_domains: Whitelist high-signal sources, reduce noise
        # - max_results: Configurable but capped to avoid overwhelming context
        response = client.search(
            query=query,
            search_depth="advanced",  # More thorough, higher quality
            topic="news",  # Focus on recent, newsworthy content
            days=args.days,  # Tavily's native time filtering
            max_results=args.max_results,
            include_domains=include_domains,
        )
    except Exception as e:
        print(f"Error: Tavily search failed: {e}", file=sys.stderr)
        sys.exit(1)

    # Normalize Tavily response into our standard format
    # Contract: Simplified structure for easy agent parsing
    results = []
    for item in response.get("results", []):
        results.append({
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            # Tavily may or may not include published_at; preserve if available
            "published_at": item.get("published_date"),
            "content": item.get("content", ""),
            # Tavily's relevance score (0-1), useful for ranking
            "score": item.get("score", 0.0),
        })

    # Build output JSON following our contract
    output_data = {
        "company": args.company,
        "search_type": "news",
        "queried_at": datetime.now(timezone.utc).isoformat(),
        "lookback_days": args.days,
        "results": results,
        "total_results": len(results),
    }

    # Write to file if requested (ensure parent directories exist)
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
                "search_type": "news",
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

