---
name: web-search-blogs
description: Search for engineering blogs, technical articles, and deep-dives about a company (last 30 days).
---

# Web Search - Blogs

Finds engineering blog posts, technical articles, and thought leadership content using targeted domain filtering.

## Script

```bash
python3 /skills/web-search-blogs/scripts/search_blogs.py "Company Name" \
  --days 30 \
  --max-results 5 \
  --output /path/to/output.json
```

**Key behavior:**
- **With `--output`**: Saves full results to file, returns 150-char summary (token-efficient)
- **Without `--output`**: Returns full JSON to stdout (~4,500 chars)

## Output (with --output flag)

```json
{
  "saved_to": "/path/to/output.json",
  "company": "LlamaIndex",
  "total_results": 2,
  "top_result": "LlamaParse update: new features...",
  "lookback_days": 30
}
```

Full file contains: title, url, published_at, content snippet, relevance score.
