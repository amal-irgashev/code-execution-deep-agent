#!/usr/bin/env python3
"""Extract full content from specific URLs using Tavily Extract API.

This is a second-tier tool for deep content retrieval. Use after search tools
have identified high-value URLs that warrant detailed analysis.

Design philosophy (context engineering):
- Search tools: Fast discovery, return summaries (token-efficient)
- Extract tool: Selective depth, save to files (keep context clean)
- Subagent workflow: Search → identify top URLs → extract → save → summarize paths

Contract:
- Input: List of URLs to extract
- Output: Saves full markdown to files, returns JSON with file paths
- Token efficiency: Agent only sees file paths, not full content
"""

import argparse
import hashlib
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


def url_to_filename(url: str) -> str:
    """Convert URL to safe filename using hash."""
    # Use first 12 chars of URL hash for uniqueness
    url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
    # Extract domain for readability
    domain = url.split('//')[-1].split('/')[0].replace('.', '-')
    return f"{domain}-{url_hash}.md"


def main():
    """Parse CLI arguments and execute Tavily extract."""
    parser = argparse.ArgumentParser(
        description="Extract full content from URLs using Tavily Extract API"
    )
    parser.add_argument(
        "urls",
        nargs="+",
        help="One or more URLs to extract content from (max 20)",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Directory to save extracted markdown files",
    )
    parser.add_argument(
        "--extract-depth",
        choices=["basic", "advanced"],
        default="advanced",
        help="Extraction depth (default: advanced for detailed content)",
    )

    args = parser.parse_args()

    # Validate inputs
    if len(args.urls) > 20:
        print(
            f"Error: Tavily Extract API supports max 20 URLs per request, got {len(args.urls)}",
            file=sys.stderr,
        )
        sys.exit(1)

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

    # Execute extract
    try:
        response = client.extract(
            urls=args.urls,
            extract_depth=args.extract_depth,
        )
    except Exception as e:
        print(f"Error: Tavily extract failed: {e}", file=sys.stderr)
        sys.exit(1)

    # Ensure output directory exists
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Process results and save to files
    extracted_files = []
    for result in response.get("results", []):
        url = result.get("url", "")
        raw_content = result.get("raw_content", "")
        
        if not raw_content:
            print(f"Warning: No content extracted from {url}", file=sys.stderr)
            continue

        # Generate filename and save
        filename = url_to_filename(url)
        filepath = output_dir / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                # Add metadata header
                f.write(f"<!-- Extracted from: {url} -->\n")
                f.write(f"<!-- Extracted at: {datetime.now(timezone.utc).isoformat()} -->\n")
                f.write(f"<!-- Content length: {len(raw_content)} chars -->\n\n")
                f.write(raw_content)
            
            extracted_files.append({
                "url": url,
                "filepath": str(filepath),
                "filename": filename,
                "size_chars": len(raw_content),
                "size_kb": round(len(raw_content) / 1024, 2),
            })
        except Exception as e:
            print(f"Error: Failed to write {filepath}: {e}", file=sys.stderr)
            continue

    # Build output JSON
    output_data = {
        "extracted_at": datetime.now(timezone.utc).isoformat(),
        "output_dir": str(output_dir),
        "files": extracted_files,
        "total_files": len(extracted_files),
        "total_size_kb": sum(f["size_kb"] for f in extracted_files),
    }

    # Print JSON to stdout for agent consumption
    print(json.dumps(output_data, indent=2))


if __name__ == "__main__":
    main()

