---
name: web-search-docs
description: Search for documentation updates, API changes, and release notes. Includes deep extraction tool.
---

# Web Search - Documentation

Two-phase workflow: fast discovery → selective deep extraction.

## Phase 1: Discovery

```bash
python3 /skills/web-search-docs/scripts/search_docs.py "Company Name" \
  --days 14 \
  --max-results 5 \
  --output /path/to/output.json
```

**With `--output`**: Returns 150-char summary, saves full results to file  
**Without `--output`**: Returns full JSON (~5,500 chars)

## Phase 2: Deep Extraction (Optional)

```bash
python3 /skills/web-search-docs/scripts/extract_detail.py \
  "https://docs.example.com/release-notes" \
  "https://docs.example.com/api-changes" \
  --output-dir /path/to/extracted/
```

Extracts 10-30x more content than search summaries. Returns file paths only (keeps context clean).

**Output:**
```json
{
  "total_files": 2,
  "total_size_kb": 39.37,
  "files": [
    {"filepath": "/path/docs-example-com-a892c538.md", "size_kb": 28.17},
    {"filepath": "/path/www-example-com-d8691d06.md", "size_kb": 11.2}
  ]
}
```

Full clean markdown saved to files, not loaded into context.
