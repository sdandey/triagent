---
name: pyspark-reviewer
description: |
  Autonomous PySpark/Databricks code review agent. Use when:
  - Reviewing PRs with .py, .ipynb, or Spark SQL files
  - Analyzing PySpark code for performance issues
  - Checking Delta Lake best practices
  - Validating Serverless SQL Warehouse compatibility
  - Reviewing Databricks notebook code
  Invoke with: /pyspark-reviewer [PR_URL or file paths]
version: 2.0.0
---

# PySpark Code Review Agent

## Agent Workflow (Autonomous Mode)

When this skill is invoked, follow these steps automatically:

### 1. Gather Context
- **If PR URL provided**: Fetch PR changes using `gh pr view` or Azure DevOps CLI
- **If file paths provided**: Read files directly using the Read tool
- **Identify target files**: Find all `.py`, `.ipynb`, `.sql` files in the changes
- **Check for Spark imports**: Identify files with `pyspark`, `spark`, `delta` imports

### 2. Analyze Code
For each file, check against the review guidelines below:
- **Performance**: UDFs, joins, partitioning, caching
- **Data Quality**: Schema, null handling, validation
- **Security**: Credentials, Unity Catalog usage
- **Code Quality**: Method chaining, column references
- **Serverless Compatibility**: Caching, UDF types

### 3. Categorize Issues
Assign severity to each finding:
| Severity | Criteria |
|----------|----------|
| **Critical** | Security risk, data loss potential, production blocker |
| **High** | Significant performance impact (>5x slower), incorrect results |
| **Medium** | Moderate performance impact, code quality issues |
| **Low** | Style, best practice suggestions, minor improvements |

### 4. Generate Report
Structure findings as:
```markdown
## PySpark Code Review Summary

### Critical Issues (X)
- [File:Line] Issue description
  - Problem: What's wrong
  - Impact: Why it matters
  - Fix: Code example

### High Issues (X)
...

### Serverless Compatibility
- [ ] No caching issues
- [ ] No unsupported UDFs
- [ ] Delta Lake optimizations used
```

### 5. Post Comments (if PR)
For each issue:
- Add inline comment at specific line
- Include severity, problem, and suggested fix
- Use code snippets for clarity

---

## PySpark Code Review Guidelines

### 1. Performance Optimization

#### 1.1 Native Functions vs UDFs

**Rule**: Always prefer Spark native functions over UDFs

| Pattern | Performance Impact |
|---------|-------------------|
| Native functions (F.col, F.when, etc.) | Baseline (fastest) |
| Vectorized/Pandas UDFs | 3-5x slower than native |
| Python UDFs | 5-10x slower than native |
| RDD operations | Avoid in DataFrame code |

**Anti-patterns to flag:**
- `df.rdd.map()` when DataFrame operations exist
- Custom Python UDFs for operations available in `pyspark.sql.functions`
- String manipulation in Python instead of F.regexp_replace, F.split

**Examples:**

```python
# BAD: Python UDF
@udf(returnType=DoubleType())
def calculate_ratio(a, b):
    return a / b if b != 0 else 0.0

# GOOD: Native function
df.withColumn("ratio", F.when(F.col("b") != 0, F.col("a") / F.col("b")).otherwise(0.0))

# BAD: Python UDF for string ops
@udf(returnType=StringType())
def clean_text(text):
    return text.strip().lower()

# GOOD: Native functions
df.withColumn("clean", F.lower(F.trim(F.col("text"))))
```

#### 1.2 Vectorized UDFs (When UDFs Unavoidable)

**Rule**: Use Pandas UDFs for complex operations not available natively

```python
# GOOD: Vectorized UDF (3-5x faster than regular UDF)
@pandas_udf(returnType=DoubleType())
def complex_calculation(values: pd.Series) -> pd.Series:
    return np.sqrt(values * 2 + 1)
```

#### 1.3 Join Optimization

| Table Size | Strategy |
|------------|----------|
| < 10MB | BROADCAST (automatic) |
| 10-100MB | BROADCAST (explicit hint recommended) |
| > 100MB | Shuffle join (default) |

**Examples:**

```python
# GOOD: Explicit broadcast hint for small dimension table
result = large_fact_df.join(
    F.broadcast(small_dim_df),
    "key"
)

# GOOD: SQL with broadcast hint
spark.sql("""
    SELECT /*+ BROADCAST(d) */
        f.fact_id, d.dimension_name
    FROM large_fact_table f
    JOIN small_dimension_table d ON f.dimension_key = d.dimension_key
""")
```

#### 1.4 Partitioning Strategy

**Read Optimization:**
- Partition on high-cardinality filter columns (date, region)
- Target 128MB-1GB per partition
- Use Z-ordering for multi-column filtering

**Write Optimization:**
- Avoid small files (< 128MB each)
- Use `coalesce()` for reducing partitions
- Use `repartition()` when increasing or redistributing

```python
# BAD: Too many small partitions
df.repartition(1000).write.parquet(path)

# GOOD: Right-sized partitions
df.coalesce(optimal_partition_count).write.parquet(path)
```

#### 1.5 Caching Strategy

**CRITICAL: Serverless SQL Warehouse Limitations**
- `df.cache()` - Does NOT work in Serverless
- `CACHE TABLE` - Does NOT work in Serverless
- Delta Lake optimizations work in both

**When to cache (Classic compute only):**
- DataFrame used 3+ times in same job
- After expensive transformations
- Before iterative algorithms

```python
# GOOD: Strategic caching (Classic compute)
df_filtered = df.filter(...).cache()
count = df_filtered.count()  # Materializes cache
result1 = df_filtered.groupBy(...).agg(...)
result2 = df_filtered.select(...)
df_filtered.unpersist()  # Always cleanup
```

#### 1.6 Collect and toPandas Anti-patterns

**Rule**: Avoid bringing large datasets to driver

```python
# BAD: Collecting all data
all_rows = df.collect()  # OOM risk!

# BAD: Converting large DataFrame to Pandas
pdf = df.toPandas()  # OOM risk!

# GOOD: Limit before collect
sample_rows = df.limit(100).collect()

# GOOD: Filter before toPandas
pdf = df.filter(F.col("category") == "A").limit(10000).toPandas()
```

### 2. SQL Query Patterns

#### 2.1 Query Structure

```sql
-- GOOD: Explicit columns, early filtering
SELECT
    customer_id,
    order_date,
    total_amount
FROM orders
WHERE order_date >= '2024-01-01'
  AND status = 'COMPLETED'

-- BAD: SELECT *, late filtering
SELECT * FROM orders
```

#### 2.2 CTEs for Readability

```sql
-- GOOD: Clear, readable CTEs
WITH active_customers AS (
    SELECT customer_id, customer_name
    FROM customers
    WHERE status = 'active'
),
recent_orders AS (
    SELECT customer_id, SUM(amount) as total
    FROM orders
    WHERE order_date >= CURRENT_DATE - INTERVAL 30 DAYS
    GROUP BY customer_id
)
SELECT ac.customer_name, ro.total
FROM active_customers ac
JOIN recent_orders ro ON ac.customer_id = ro.customer_id
```

#### 2.3 EXISTS vs JOIN

```sql
-- GOOD: EXISTS for existence check (often faster)
SELECT *
FROM orders o
WHERE EXISTS (
    SELECT 1 FROM customers c
    WHERE c.customer_id = o.customer_id
    AND c.status = 'active'
)

-- BAD: JOIN just for filtering
SELECT o.*
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
WHERE c.status = 'active'
```

#### 2.4 UNION ALL vs UNION

```sql
-- GOOD: UNION ALL when duplicates impossible or acceptable
SELECT customer_id FROM orders_2023
UNION ALL
SELECT customer_id FROM orders_2024

-- BAD: UNION when UNION ALL works (unnecessary sort)
SELECT customer_id FROM orders_2023
UNION
SELECT customer_id FROM orders_2024
```

#### 2.5 Anti-join Patterns

```sql
-- GOOD: LEFT ANTI JOIN for "not exists"
SELECT o.*
FROM orders o
LEFT ANTI JOIN cancelled_orders c ON o.order_id = c.order_id

-- Alternative: NOT EXISTS
SELECT o.*
FROM orders o
WHERE NOT EXISTS (
    SELECT 1 FROM cancelled_orders c
    WHERE c.order_id = o.order_id
)
```

### 3. Delta Lake Best Practices

#### 3.1 Table Maintenance

```sql
-- Required: Analyze for query optimizer
ANALYZE TABLE catalog.schema.table COMPUTE STATISTICS FOR ALL COLUMNS;

-- Required: Compact small files (run weekly or after large writes)
OPTIMIZE catalog.schema.table ZORDER BY (frequently_filtered_column);

-- Required: Cleanup old versions (run weekly, respects retention)
VACUUM catalog.schema.table RETAIN 168 HOURS;
```

#### 3.2 Z-Ordering vs Liquid Clustering

| Feature | Z-Ordering | Liquid Clustering |
|---------|-----------|-------------------|
| Performance | 40-80% improvement | Similar or better |
| Maintenance | Manual OPTIMIZE | Automatic |
| Use case | Static tables | Active tables |
| Runtime | Any | Databricks Runtime 13.3+ |

```sql
-- Z-ordering (manual maintenance required)
OPTIMIZE table ZORDER BY (region, date);

-- Liquid Clustering (automatic, Databricks Runtime 13.3+)
CREATE TABLE catalog.schema.table CLUSTER BY (region, date);

-- Alter existing table to use Liquid Clustering
ALTER TABLE catalog.schema.table CLUSTER BY (region, date);
```

#### 3.3 Schema Evolution

```python
# GOOD: Allow schema evolution for appends
df.write.format("delta") \
    .mode("append") \
    .option("mergeSchema", "true") \
    .saveAsTable("catalog.schema.table")

# GOOD: Overwrite with schema replacement (breaking change)
df.write.format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .saveAsTable("catalog.schema.table")
```

#### 3.4 Time Travel

```sql
-- Query historical data
SELECT * FROM catalog.schema.table VERSION AS OF 5;
SELECT * FROM catalog.schema.table TIMESTAMP AS OF '2024-01-15 10:00:00';

-- Restore to previous version
RESTORE TABLE catalog.schema.table TO VERSION AS OF 5;
```

### 4. Security & Credentials

#### 4.1 Secrets Management

```python
# BAD: Hardcoded credentials
password = "my_secret_password"
connection_string = "Server=myserver;Database=mydb;User=admin;Password=secret123"

# BAD: Environment variables in notebooks
password = os.environ["PASSWORD"]

# GOOD: Databricks secrets
password = dbutils.secrets.get(scope="my-scope", key="my-password")
connection_string = dbutils.secrets.get(scope="my-scope", key="connection-string")
```

#### 4.2 Unity Catalog

- Always use three-level namespace: `catalog.schema.table`
- Never grant direct storage access to users
- Use Unity Catalog for all access control
- Prefer views for row-level security

```python
# GOOD: Unity Catalog three-level namespace
df = spark.read.table("cortex_prd_catalog.engagement.orders")

# BAD: Direct path access (bypasses security)
df = spark.read.parquet("abfss://container@storage.dfs.core.windows.net/path")
```

### 5. Code Quality

#### 5.1 Method Chaining

```python
# BAD: Repeated variable assignment
df1 = df.filter(F.col("status") == "active")
df2 = df1.withColumn("total", F.col("price") * F.col("quantity"))
df3 = df2.select("customer_id", "total")
result = df3.groupBy("customer_id").agg(F.sum("total"))

# GOOD: Method chaining with line breaks
result = (
    df
    .filter(F.col("status") == "active")
    .withColumn("total", F.col("price") * F.col("quantity"))
    .select("customer_id", "total")
    .groupBy("customer_id")
    .agg(F.sum("total"))
)
```

#### 5.2 Column References

```python
# BAD: String column names (no IDE support, typos not caught)
df.select("customer_name", "order_date")
df.filter(df["status"] == "active")

# GOOD: F.col() for explicit column references
df.select(F.col("customer_name"), F.col("order_date"))
df.filter(F.col("status") == "active")
```

#### 5.3 Schema Definition

```python
# BAD: Schema inference (slow, inconsistent)
df = spark.read.json(path)  # Infers schema

# GOOD: Explicit schema definition
schema = StructType([
    StructField("customer_id", StringType(), nullable=False),
    StructField("order_date", DateType(), nullable=False),
    StructField("amount", DecimalType(18, 2), nullable=True),
])
df = spark.read.schema(schema).json(path)
```

#### 5.4 Null Handling

```python
# BAD: No null handling
df.withColumn("ratio", F.col("a") / F.col("b"))  # NullPointerException risk

# GOOD: Explicit null handling
df.withColumn(
    "ratio",
    F.when(F.col("b").isNotNull() & (F.col("b") != 0), F.col("a") / F.col("b"))
    .otherwise(F.lit(None))
)

# GOOD: Use coalesce for defaults
df.withColumn("name", F.coalesce(F.col("name"), F.lit("Unknown")))
```

### 6. Serverless Compatibility Reference

| Feature | Classic Compute | Serverless SQL Warehouse |
|---------|----------------|-------------------------|
| DataFrame caching | Supported | NOT Supported |
| CACHE TABLE | Supported | NOT Supported |
| Spark UI | Available | NOT Available |
| Custom JARs | Supported | NOT Supported |
| Scala UDFs | Supported | NOT Supported |
| Python UDFs | Supported | Supported |
| SQL UDFs | Supported | Supported |
| Delta Lake | Supported | Supported |
| Unity Catalog | Supported | Supported |
| Photon | Configurable | Always enabled |
| AQE | Configurable | Always enabled |

**Serverless-safe code checklist:**
- No `df.cache()` or `.persist()`
- No `spark.catalog.cacheTable()`
- No custom Scala/Java UDFs
- Use Delta Lake optimizations instead of caching
- Use query hints for join optimization

### 7. Error Handling & Reliability

#### 7.1 Checkpointing

```python
# GOOD: Checkpoint for long lineages
spark.sparkContext.setCheckpointDir("/tmp/checkpoints")

df_complex = df.transform(transformation_1).transform(transformation_2)
df_checkpointed = df_complex.checkpoint()  # Breaks lineage, enables recovery
```

#### 7.2 Idempotent Writes

```python
# GOOD: Idempotent merge for upserts
spark.sql("""
    MERGE INTO target t
    USING source s ON t.id = s.id
    WHEN MATCHED THEN UPDATE SET *
    WHEN NOT MATCHED THEN INSERT *
""")

# GOOD: Partition overwrite for daily loads
df.write.format("delta") \
    .mode("overwrite") \
    .option("replaceWhere", f"date = '{target_date}'") \
    .saveAsTable("catalog.schema.table")
```

### 8. Code Review Checklist

**Performance:**
- [ ] No Python UDFs when native functions exist
- [ ] Broadcast hints for small dimension tables (< 100MB)
- [ ] Appropriate partitioning strategy
- [ ] No unnecessary `collect()` or `toPandas()`
- [ ] Cache cleanup with `unpersist()` (Classic compute)
- [ ] No `SELECT *` in production queries

**Data Quality:**
- [ ] Schema defined explicitly, not inferred
- [ ] Null handling with `coalesce()` or explicit checks
- [ ] Delta table maintenance scheduled (ANALYZE, OPTIMIZE, VACUUM)
- [ ] Data validation checks before writes

**Security:**
- [ ] Credentials via `dbutils.secrets.get()`
- [ ] Unity Catalog three-level namespace used
- [ ] No hardcoded secrets or connection strings
- [ ] No direct storage path access (bypasses security)

**Code Quality:**
- [ ] Method chaining for transformations
- [ ] F.col() for column references
- [ ] Descriptive variable names
- [ ] Comments for complex business logic

**Serverless Compatibility:**
- [ ] No caching if targeting Serverless
- [ ] No Scala/Java UDFs
- [ ] Delta Lake optimizations used instead

### 9. Review Process

1. Fetch PR changes using Azure DevOps CLI or gh CLI
2. Identify Spark files (.py with spark imports, .ipynb)
3. Check for performance anti-patterns:
   - Python UDFs that could be native functions
   - Missing broadcast hints for small tables
   - `collect()` or `toPandas()` on large DataFrames
4. Verify Serverless compatibility if applicable
5. Check Delta Lake best practices (maintenance commands, schema evolution)
6. Validate security patterns (secrets, Unity Catalog)
7. Post inline comments with:
   - File path and line number
   - Severity (Critical/High/Medium/Low)
   - Problem description
   - Code example of the fix
