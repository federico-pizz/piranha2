# Redis - In-Memory Data Store

## What is Redis?

Redis (Remote Dictionary Server) is an **in-memory data structure store**. Think of it as a super-fast dictionary that lives in RAM instead of on disk.

### Why is it "super-important"?

1. **Speed**: Redis operates at ~100,000+ operations per second because it stores data in memory
2. **Caching**: Avoid hitting the database repeatedly for the same data
3. **Sessions**: Store user sessions without database queries
4. **Job Queues**: Background task management (like our scraper jobs)
5. **Real-time features**: Pub/sub for live updates

### Real-World Analogy

Imagine a library:
- **PostgreSQL** = The library's book storage (permanent, organized, but takes time to retrieve)
- **Redis** = The librarian's desk with frequently requested books (fast access, limited space)

---

## How Piranha ITA Uses Redis

### 1. Caching Product Searches
```
User searches "iPhone" → Check Redis first → If cached, return immediately
                                           → If not, query PostgreSQL, cache result
```

### 2. Rate Limiting
```
Track API requests per user → Block if too many requests
```

### 3. Session Storage
```
User logs in → Store session token in Redis → Fast authentication checks
```

### 4. Background Job Queue (Future)
```
Scraper job scheduled → Add to Redis queue → Worker picks up and executes
```

---

## Redis Data Types

Redis isn't just key-value. It supports multiple data structures:

| Type | Description | Example Use |
|------|-------------|-------------|
| **String** | Simple key-value | Cache a product JSON |
| **Hash** | Object with fields | User session data |
| **List** | Ordered collection | Job queue |
| **Set** | Unique values | Track online users |
| **Sorted Set** | Ranked values | Leaderboards, trending |
| **Streams** | Event log | Real-time notifications |

---

## Basic Redis Commands

### Connecting to Redis

```bash
# Enter the Redis container
sudo docker exec -it piranha2-redis-1 redis-cli

# Or connect from host (if redis-cli installed locally)
redis-cli -h localhost -p 6379
```

### String Operations

```redis
# Set a value
SET mykey "Hello World"

# Get a value
GET mykey
# Returns: "Hello World"

# Set with expiration (60 seconds)
SET cache:product:123 '{"name":"iPhone"}' EX 60

# Check remaining time
TTL cache:product:123
# Returns: 58 (seconds left)

# Delete a key
DEL mykey
```

### Working with Hashes (Objects)

```redis
# Store a user session
HSET session:abc123 user_id 1 email "user@example.com" role "user"

# Get specific field
HGET session:abc123 email
# Returns: "user@example.com"

# Get all fields
HGETALL session:abc123
# Returns all key-value pairs

# Set expiration on the hash
EXPIRE session:abc123 3600  # 1 hour
```

### Lists (Queues)

```redis
# Add to queue (left push)
LPUSH job:scrape "ebay" "discogs" "reverb"

# Get queue length
LLEN job:scrape
# Returns: 3

# Pop from queue (right pop - FIFO)
RPOP job:scrape
# Returns: "ebay"

# View items without removing
LRANGE job:scrape 0 -1
# Returns all items
```

### Sets (Unique Values)

```redis
# Add to set
SADD active:users "user1" "user2" "user3"

# Check if member exists
SISMEMBER active:users "user1"
# Returns: 1 (true)

# Get all members
SMEMBERS active:users

# Remove from set
SREM active:users "user1"
```

---

## Useful Admin Commands

```redis
# See all keys (use sparingly in production!)
KEYS *

# Count all keys
DBSIZE

# Get server info
INFO

# Get memory usage
INFO memory

# Clear everything (DANGEROUS!)
FLUSHALL

# Monitor all commands in real-time
MONITOR
# Press Ctrl+C to stop
```

---

## Common Patterns

### 1. Cache-Aside Pattern

```python
def get_product(product_id):
    # Try cache first
    cached = redis.get(f"product:{product_id}")
    if cached:
        return json.loads(cached)
    
    # Cache miss - get from database
    product = db.query(Product).get(product_id)
    
    # Store in cache for 5 minutes
    redis.setex(f"product:{product_id}", 300, json.dumps(product))
    
    return product
```

### 2. Rate Limiting

```python
def check_rate_limit(user_id, limit=100, window=3600):
    key = f"ratelimit:{user_id}"
    current = redis.incr(key)
    
    if current == 1:
        redis.expire(key, window)  # Set expiry on first request
    
    return current <= limit
```

### 3. Distributed Locking

```python
def acquire_lock(lock_name, timeout=10):
    # NX = only set if not exists
    # EX = expire in seconds
    return redis.set(f"lock:{lock_name}", "1", nx=True, ex=timeout)

def release_lock(lock_name):
    redis.delete(f"lock:{lock_name}")
```

---

## Configuration in Piranha ITA

### docker-compose.yml
```yaml
redis:
  image: redis:7-alpine
  ports:
    - "6379:6379"
  volumes:
    - redis_data:/data  # Persist data between restarts
  healthcheck:
    test: ["CMD", "redis-cli", "ping"]
```

### Environment Variable
```bash
REDIS_URL=redis://redis:6379/0
```

The `/0` means database 0 (Redis has 16 databases by default, 0-15).

---

## Monitoring Redis

### Memory Usage
```redis
INFO memory
# Look for: used_memory_human
```

### Connected Clients
```redis
CLIENT LIST
```

### Slow Commands
```redis
SLOWLOG GET 10
```

---

## When NOT to Use Redis

- **Persistent primary data** → Use PostgreSQL
- **Complex queries** → Use PostgreSQL  
- **Data larger than RAM** → Use PostgreSQL
- **ACID transactions** → Use PostgreSQL

Redis is a **cache and helper**, not a replacement for your database.

---

## Troubleshooting

### Redis Won't Start
```bash
sudo docker logs piranha2-redis-1
# Check for memory issues or config errors
```

### Out of Memory
```redis
# Check memory
INFO memory

# Set max memory (in redis.conf or command)
CONFIG SET maxmemory 256mb
CONFIG SET maxmemory-policy allkeys-lru
```

### Connection Refused
```bash
# Check if running
sudo docker ps | grep redis

# Check port
sudo lsof -i :6379
```
