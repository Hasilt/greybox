# Redis: In-Memory Data Store

Redis is an open-source, in-memory key-value database that serves as a cache, message broker, and session store across millions of production deployments. Built for speed, it offers atomic operations, sophisticated data types, and expiration semantics that make it ideal for real-time applications and the caching tier of RAG systems.

## Core Architecture and Key-Value Model

Redis operates as a single-threaded, in-memory database where all data resides in RAM. This design eliminates disk I/O latency for reads and writes, delivering microsecond-level response times. All data is keyed by strings, and each key maps to a value of a specific type. The single-threaded model ensures atomicity: operations execute completely before the next command is processed, eliminating race conditions common in multi-threaded systems.

Keys can be as simple as user IDs ("user:123") or compound identifiers ("document:article-42:metadata"). Naming conventions using colons as delimiters are standard practice for organizing conceptually related data.

## Rich Data Types

Beyond simple strings, Redis supports several sophisticated data structures:

**Strings** are the most basic type, storing text or binary data up to 512 MB. Atomic string operations include APPEND, INCR (increment), and DECR (decrement), useful for counters and metrics.

**Hashes** store field-value mappings, similar to objects or dictionaries. They are memory-efficient for storing structured data like user profiles or document metadata without serialization overhead. Operations include HSET, HGET, HGETALL, and HINCRBY.

**Lists** are ordered collections of strings, supporting push/pop operations from either end (LPUSH, RPUSH, LPOP, RPOP). They are ideal for queues and activity streams.

**Sets** are unordered collections of unique strings, supporting membership testing and set operations (UNION, INTERSECTION, DIFFERENCE) efficiently.

**Sorted Sets** combine sets with scores: each member has an associated numeric score, and elements are ordered by score. ZRANGE queries retrieve members within score ranges, perfect for leaderboards, time-series data, or ranked search results.

## Key Expiration and Time-to-Live (TTL)

Redis supports automatic expiration of keys, essential for cache coherency and memory management. The **EXPIRE** command sets a key's time-to-live in seconds; **PEXPIRE** sets it in milliseconds for finer granularity. Once the TTL elapses, Redis automatically deletes the key, freeing memory.

You can check a key's remaining TTL with the **TTL** command (returns seconds) or **PTTL** (returns milliseconds). TTL returns -1 for keys with no expiration and -2 for keys that don't exist.

Expiration is precise to milliseconds on modern Redis versions. This is crucial for RAG caching: embedding cache entries can expire after hours, conversation history after days, and token counts within seconds if needed.

## Eviction Policies

When Redis reaches maximum memory (configured via **maxmemory**), eviction policies determine what happens. The **noeviction** policy rejects writes once full, suitable for critical data where loss is unacceptable. 

**allkeys-lru** evicts the least recently used key across all keys, balancing fairness across application data. **volatile-lru** only evicts keys with TTL set, preserving persistent data. This hybrid approach is common: cache data has expiration, core data does not.

**allkeys-lfu** evicts based on least frequency of use (how many times accessed), better than LRU for workloads with temporal access patterns. **volatile-lfu** applies LFU only to expiring keys.

For RAG systems, **allkeys-lru** is typical for embedding caches; keys are evicted as memory fills, and TTL ensures old entries are eventually purged.

## Persistence Strategies

Although Redis is in-memory, it offers two persistence mechanisms for durability:

**RDB (Redis Database Snapshots)** creates point-in-time binary snapshots of the entire dataset, triggered by BGSAVE or scheduled via save policies (e.g., "save every 60 seconds if 1000 keys changed"). Snapshots are compact but offer coarse granularity: any writes between snapshots are lost on crash.

**AOF (Append-Only File)** logs every write command to disk in real time. On restart, Redis replays the log to reconstruct state. AOF is more durable (fsync can be immediate) but slower and produces larger files. Periodic AOF rewriting compacts the log.

Production deployments often combine both: RDB for bulk recovery speed and AOF for durability of recent transactions.

## Publish/Subscribe (Pub/Sub)

Redis supports publisher-subscriber messaging: clients SUBSCRIBE to channels and receive messages published by other clients. This is fundamentally different from queues (Pub/Sub discards messages if no subscribers are listening). Pub/Sub is useful for real-time notifications, cache invalidation signals, and event streaming in RAG pipelines.

Channels support pattern subscriptions (e.g., PSUBSCRIBE "document:*") for dynamic topic management.

## Atomic Operations and Transactions

Redis guarantees atomicity of individual commands. Complex multi-step operations can be grouped with MULTI/EXEC transactions. All commands between MULTI and EXEC are queued and executed as an atomic block. WATCH enables optimistic locking: if watched keys change before EXEC, the transaction aborts.

For RAG embeddings, transactions ensure consistency: you can atomically check cache availability, retrieve a value, and update a hit-count field without interleaving updates from other clients.

## Common RAG Use Cases

In retrieval systems, Redis caches embedding vectors and similarity search results, reducing recomputation. Query embeddings can be cached if the same queries repeat. Embedding models themselves are not typically stored in Redis (too large), but metadata—embedding timestamps, model versions, and centroid vectors for drift detection—are. Session state in conversational RAG stores recent context and token counts.

TTL management ensures caches self-clean: stale embeddings expire automatically, and conversation memory can be pruned by session age.
