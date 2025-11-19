---
name: web-search-news
description: Search for recent news, press releases, and announcements about a company (last 7 days).
---

# Web Search - News

Finds breaking news, product launches, partnerships, and press releases using Tavily's news-focused search with domain filtering.

## Script

```bash
python3 /skills/web-search-news/scripts/search_news.py "Company Name" \
  --days 7 \
  --max-results 5 \
  --output /path/to/output.json
```

**Key behavior:**
- **With `--output`**: Saves full results to file, returns 150-char summary (token-efficient)
- **Without `--output`**: Returns full JSON to stdout (~5,000 chars)

## Output (with --output flag)

```json
{
  "saved_to": "/path/to/output.json",
  "company": "Anthropic",
  "total_results": 3,
  "top_result": "Microsoft partnership announcement...",
  "lookback_days": 7
}
```

Full file contains: title, url, published_at, content snippet, relevance score.
