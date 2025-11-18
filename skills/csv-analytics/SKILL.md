---
name: csv-analytics
description: Analyze large CSV files using efficient filtering and aggregation. Use when user asks about CSV data, trends, summaries, or top/bottom records.
---

# CSV Analytics Skill

This skill provides efficient tools for analyzing CSV files, especially large ones with thousands of rows. Instead of loading entire CSVs into the conversation context, use these scripts to perform filtering, sorting, and aggregation off-model.

## When to Use This Skill

Use this skill when the user:
- Asks about CSV files or tabular data
- Wants to find top/bottom records by some criteria
- Needs filtering based on numeric or text conditions
- Wants summary statistics or aggregations
- Has a dataset with >1000 rows (to avoid context bloat)

## Available Scripts

### filter_high_value.py

Filters CSV rows where a numeric column exceeds a threshold and returns top N results.

**Usage:**
```bash
python3 /skills/csv-analytics/scripts/filter_high_value.py <csv_path> <column_name> <threshold> [--top N]
```

**Arguments:**
- `csv_path`: Path to the CSV file
- `column_name`: Name of the numeric column to filter/sort by
- `threshold`: Minimum value to include (optional, defaults to 0)
- `--top N`: Return only top N rows (default: 10)

**Output:** JSON array of matching rows sorted by column in descending order

**Example:**
```bash
# Find top 5 orders with amount > 1000
python3 /skills/csv-analytics/scripts/filter_high_value.py /workspace/data/orders.csv amount 1000 --top 5
```

## Supporting Documentation

For more advanced usage patterns, see:
- `/skills/csv-analytics/docs/aggregation.md` - Grouping and aggregation techniques

## Best Practices

1. **Always use scripts for large datasets**: If CSV has >1000 rows, don't read the entire file
2. **Filter before context**: Run scripts to filter data, then summarize the filtered results
3. **Check column names first**: Use `read_file` to peek at the first few lines to see column names
4. **Explain to user**: Tell the user you're using efficient filtering to avoid loading all data

## Example Workflow

User asks: "What are the top 5 orders by amount in orders.csv?"

1. You: Check if file exists with `ls /workspace/data/`
2. You: Peek at first lines with `read_file(/workspace/data/orders.csv, limit=5)` to see columns
3. You: Run `execute("python3 /skills/csv-analytics/scripts/filter_high_value.py /workspace/data/orders.csv amount 0 --top 5")`
4. You: Parse JSON output and present summary to user in natural language

## Notes

- Scripts use pandas for fast, memory-efficient processing
- All scripts output JSON to stdout for easy parsing
- Error messages go to stderr (will appear in execute output)

