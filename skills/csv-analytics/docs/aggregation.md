# CSV Aggregation and Grouping

This document explains advanced aggregation techniques for CSV analysis using pandas.

## Common Aggregation Patterns

### Grouping and Summarization

When analyzing CSV data, you often want to group rows by one or more columns and compute aggregate statistics:

```python
# Group by category and sum amounts
df.groupby('category')['amount'].sum()

# Multiple aggregations
df.groupby('category').agg({
    'amount': ['sum', 'mean', 'count'],
    'quantity': 'sum'
})
```

### Time-based Aggregation

For time-series data with date columns:

```python
# Convert to datetime
df['date'] = pd.to_datetime(df['date'])

# Group by month and sum
df.groupby(df['date'].dt.to_period('M'))['amount'].sum()

# Group by day of week
df.groupby(df['date'].dt.dayofweek)['amount'].mean()
```

## When to Use Scripts vs Manual Analysis

**Use Scripts When:**
- Dataset has >1000 rows
- You need filtering before aggregation
- Results will be concise (< 50 rows)
- User wants top/bottom N records

**Use Manual Analysis When:**
- Dataset is small (< 100 rows)
- User wants to explore data interactively
- Results are already filtered
- Quick summary statistics are sufficient

## Example: Complex Aggregation

For queries like "Show total sales by region and category":

1. Create a custom script (or extend filter_high_value.py)
2. Perform groupby with multiple columns
3. Output results as JSON
4. Agent parses JSON and presents to user

## Performance Tips

- **Use column selection**: Only read columns you need
- **Filter early**: Apply filters before aggregation
- **Use appropriate dtypes**: Specify data types when reading CSV
- **Chunk processing**: For very large files (>1GB), process in chunks

## Memory Considerations

Pandas loads entire CSV into memory. For files larger than available RAM:
- Use chunking: `pd.read_csv(path, chunksize=10000)`
- Use dask: A parallel computing library for larger-than-memory datasets
- Use database: Import CSV to SQLite for SQL-based queries

