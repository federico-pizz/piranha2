# PostgreSQL - Relational Database

## What is PostgreSQL?

PostgreSQL (often called "Postgres") is a powerful, open-source **relational database**. It stores your data in tables with rows and columns, like a super-powered spreadsheet that can handle millions of records.

### Why PostgreSQL?

1. **ACID Compliant**: Transactions are reliable (won't lose data)
2. **SQL Standard**: Industry-standard query language
3. **JSON Support**: Can store and query JSON documents
4. **Full-Text Search**: Built-in search capabilities
5. **Extensions**: PostGIS for geo, pgvector for AI embeddings
6. **Battle-Tested**: Used by Apple, Spotify, Instagram

---

## How Piranha ITA Uses PostgreSQL

### Main Tables

```
┌─────────────────┐     ┌─────────────────┐
│     users       │     │    products     │
├─────────────────┤     ├─────────────────┤
│ id (UUID)       │     │ id (UUID)       │
│ email           │     │ title           │
│ password_hash   │     │ description     │
│ created_at      │     │ price_eur       │
└─────────────────┘     │ category        │
         │              │ condition       │
         │              │ source_name     │
         ▼              │ source_url      │
┌─────────────────┐     │ region          │
│  interactions   │     │ scraped_at      │
├─────────────────┤     └─────────────────┘
│ user_id (FK)    │
│ product_id (FK) │
│ action_type     │
│ timestamp       │
└─────────────────┘
```

---

## Connecting to PostgreSQL

### Via Docker
```bash
# Enter psql shell
sudo docker exec -it piranha2-db-1 psql -U piranha -d piranha

# Run a single command
sudo docker exec -it piranha2-db-1 psql -U piranha -d piranha -c "SELECT COUNT(*) FROM products;"
```

### Connection String
```
postgresql://piranha:yourpassword@localhost:5432/piranha
            ───────  ────────────  ─────────  ────  ──────
              user     password      host     port  database
```

---

## Essential psql Commands

### Navigation
```sql
\l              -- List all databases
\c piranha      -- Connect to database
\dt             -- List all tables
\d products     -- Describe table structure
\d+ products    -- Detailed table info (with size)
\dn             -- List schemas
\df             -- List functions
\q              -- Quit psql
```

### Query Shortcuts
```sql
\x              -- Toggle expanded display (vertical output)
\timing         -- Show query execution time
\e              -- Open query in $EDITOR
\i file.sql     -- Execute SQL file
```

---

## Common SQL Queries

### Basic SELECT
```sql
-- Get all products
SELECT * FROM products;

-- Get specific columns
SELECT title, price_eur, condition FROM products;

-- Limit results
SELECT * FROM products LIMIT 10;

-- Order by price
SELECT * FROM products ORDER BY price_eur DESC LIMIT 10;
```

### Filtering with WHERE
```sql
-- Products under €100
SELECT * FROM products WHERE price_eur < 100;

-- Products in a category
SELECT * FROM products WHERE category = 'elettronica';

-- Multiple conditions
SELECT * FROM products 
WHERE category = 'auto' 
  AND price_eur BETWEEN 5000 AND 15000
  AND condition = 'buono';

-- Search in text
SELECT * FROM products WHERE title ILIKE '%iphone%';
-- ILIKE = case-insensitive LIKE
```

### Aggregations
```sql
-- Count products per category
SELECT category, COUNT(*) as count 
FROM products 
GROUP BY category 
ORDER BY count DESC;

-- Average price per category
SELECT category, 
       ROUND(AVG(price_eur)::numeric, 2) as avg_price,
       MIN(price_eur) as min_price,
       MAX(price_eur) as max_price
FROM products 
GROUP BY category;

-- Products scraped today
SELECT COUNT(*) FROM products 
WHERE scraped_at >= CURRENT_DATE;
```

### Joins
```sql
-- Get user interactions with product details
SELECT u.email, p.title, i.action_type, i.created_at
FROM interactions i
JOIN users u ON i.user_id = u.id
JOIN products p ON i.product_id = p.id
WHERE u.email = 'user@example.com';
```

---

## Data Modification

### INSERT
```sql
-- Insert a product
INSERT INTO products (id, title, price_eur, category, source_name, source_url)
VALUES (
    gen_random_uuid(),
    'Test Product',
    99.99,
    'elettronica',
    'manual',
    'https://example.com'
);
```

### UPDATE
```sql
-- Update price
UPDATE products 
SET price_eur = 89.99 
WHERE title = 'Test Product';

-- Update multiple columns
UPDATE products 
SET price_eur = 79.99, condition = 'buono'
WHERE id = 'some-uuid-here';
```

### DELETE
```sql
-- Delete old products (over 30 days)
DELETE FROM products 
WHERE scraped_at < NOW() - INTERVAL '30 days';

-- Delete by source
DELETE FROM products WHERE source_name = 'mock_dev';
```

---

## Indexes

Indexes make queries faster by creating lookup structures:

### View Existing Indexes
```sql
\di                           -- List all indexes
\d products                   -- See indexes on a table
```

### Create Index
```sql
-- Speed up category filtering
CREATE INDEX idx_products_category ON products(category);

-- Speed up price range queries
CREATE INDEX idx_products_price ON products(price_eur);

-- Compound index for common filter combo
CREATE INDEX idx_products_cat_price ON products(category, price_eur);

-- Full-text search index
CREATE INDEX idx_products_search ON products 
USING GIN (to_tsvector('italian', title || ' ' || description));
```

### When to Add Indexes
- Columns in WHERE clauses
- Columns in JOIN conditions
- Columns in ORDER BY
- Foreign key columns

---

## Transactions

Transactions ensure data integrity:

```sql
BEGIN;  -- Start transaction

UPDATE accounts SET balance = balance - 100 WHERE id = 1;
UPDATE accounts SET balance = balance + 100 WHERE id = 2;

-- If both succeed:
COMMIT;

-- If something went wrong:
ROLLBACK;
```

---

## Backup & Restore

### Backup
```bash
# Full backup
sudo docker exec piranha2-db-1 pg_dump -U piranha piranha > backup.sql

# Compressed backup
sudo docker exec piranha2-db-1 pg_dump -U piranha -Fc piranha > backup.dump

# Backup specific table
sudo docker exec piranha2-db-1 pg_dump -U piranha -t products piranha > products.sql
```

### Restore
```bash
# From SQL file
cat backup.sql | sudo docker exec -i piranha2-db-1 psql -U piranha -d piranha

# From compressed dump
sudo docker exec -i piranha2-db-1 pg_restore -U piranha -d piranha < backup.dump
```

---

## Performance Monitoring

### Slow Queries
```sql
-- Enable query logging (in postgresql.conf)
-- log_min_duration_statement = 1000  -- Log queries over 1 second

-- Check current connections
SELECT * FROM pg_stat_activity;

-- Kill a stuck query
SELECT pg_terminate_backend(pid) FROM pg_stat_activity 
WHERE query LIKE '%stuck_query%';
```

### Table Statistics
```sql
-- Table sizes
SELECT relname as table, 
       pg_size_pretty(pg_total_relation_size(relid)) as size
FROM pg_catalog.pg_statio_user_tables
ORDER BY pg_total_relation_size(relid) DESC;

-- Row counts
SELECT schemaname, relname, n_live_tup as row_count
FROM pg_stat_user_tables
ORDER BY n_live_tup DESC;
```

### Explain Queries
```sql
-- See query plan
EXPLAIN SELECT * FROM products WHERE category = 'auto';

-- With execution stats
EXPLAIN ANALYZE SELECT * FROM products WHERE category = 'auto';
```

---

## Configuration in Piranha ITA

### docker-compose.yml
```yaml
db:
  image: postgres:15-alpine
  environment:
    POSTGRES_USER: piranha
    POSTGRES_PASSWORD: yourpassword
    POSTGRES_DB: piranha
  ports:
    - "5432:5432"
  volumes:
    - postgres_data:/var/lib/postgresql/data
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U piranha"]
```

### Environment Variable
```bash
DATABASE_URL=postgresql://piranha:yourpassword@db:5432/piranha
```

---

## Troubleshooting

### Connection Refused
```bash
# Check if running
sudo docker ps | grep db

# Check logs
sudo docker logs piranha2-db-1

# Check port
sudo lsof -i :5432
```

### Database Locked
```sql
-- See locks
SELECT * FROM pg_locks;

-- Find blocking queries
SELECT blocked_locks.pid AS blocked_pid,
       blocking_locks.pid AS blocking_pid,
       blocked_activity.query AS blocked_statement,
       blocking_activity.query AS blocking_statement
FROM pg_catalog.pg_locks blocked_locks
JOIN pg_catalog.pg_locks blocking_locks 
    ON blocking_locks.locktype = blocked_locks.locktype
-- (simplified query)
```

### Reset Database
```bash
# ⚠️ DESTROYS ALL DATA
sudo docker-compose down -v
sudo docker-compose up -d
```
