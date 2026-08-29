# Qdrant Vector Database

Qdrant is a specialized vector database designed for efficient similarity search and retrieval-augmented generation (RAG) workloads. Built in Rust, it prioritizes high throughput, low latency, and production reliability while offering rich querying capabilities for vector data at scale.

## Collections and Vector Storage

At the core of Qdrant are collections—logical storage units that hold vectors and associated metadata. Each collection represents an independent vector space and is configured with a specific vector dimensionality and distance metric upon creation. Collections are the primary organizational unit; you cannot change these settings after creation without re-indexing. Each vector in a collection is identified by a unique point ID, which can be either a 64-bit unsigned integer or a UUID string.

Vectors in Qdrant are stored as dense arrays of floating-point numbers. The dimensionality must be consistent across all points in a collection—for example, vectors from a sentence-transformers embedding model like bge-small-en-v1.5 have exactly 384 dimensions. This uniformity is essential for the distance calculations that power similarity search.

## Payloads and Metadata Association

Beyond the vector itself, Qdrant supports attaching payloads—arbitrary JSON metadata—to each point. Payloads are a powerful feature for storing document identifiers, text chunks, URLs, timestamps, or any domain-specific attributes. This metadata remains searchable and filterable without requiring separate database lookups. For RAG systems, payloads commonly hold the original text snippet, document source, chunk index, and retrieval confidence scores.

Payloads are indexed independently from vectors, enabling filtered search: you can retrieve vectors matching both similarity criteria AND payload conditions in a single query.

## Distance Metrics and Similarity Computation

Qdrant supports three primary distance metrics, each suitable for different use cases:

**Cosine Distance** measures the angle between vectors, ranging from 0 (identical direction) to 2 (opposite direction). Cosine similarity is invariant to vector magnitude, making it ideal for normalized embeddings. Most sentence-transformer embeddings (including bge-small) are normalized, so cosine distance is the conventional choice for RAG.

**Dot Product** computes the raw inner product between vectors. It is faster than cosine on normalized vectors (mathematically equivalent after normalization) but sensitive to magnitude for unnormalized embeddings. Used when vectors are pre-normalized during embedding.

**Euclidean Distance** is the straight-line distance in vector space (L2 norm). It is geometrically intuitive and suitable for some ML pipelines, but generally slower than cosine or dot product for high-dimensional spaces.

The choice of distance metric is defined at collection creation time and affects both indexing strategy and query semantics.

## Upserts and Point Operations

Qdrant provides upsert operations—insert-or-update semantics—that simplify bulk ingestion. An upsert with an existing point ID will replace the vector and payload; a new ID creates a fresh point. Upserts are atomic and efficient, making them suitable for incremental indexing during data preparation.

Batch upserts can process thousands of points in a single request, significantly reducing network latency compared to point-by-point inserts. The API returns detailed stats on points inserted, updated, and failed.

## Filtering Capabilities

Qdrant's filtering engine allows rich boolean conditions on payloads, enabling targeted similarity search. You can filter by equality, range (numeric comparisons), string matching, geospatial bounding boxes, and complex nested conditions using AND/OR/NOT logic.

For example, in a RAG system you might search for "embedding cosine distance" while filtering to only documents from "qdrant.md" and with a timestamp within the last week. Filtering is applied server-side during the search phase, reducing data transfer and improving query efficiency.

## Persistence and Snapshots

Qdrant persists all data to disk automatically, ensuring durability across restarts. The default persistence strategy uses periodic snapshots, creating point-in-time backups of the entire collection state. Snapshots are atomic and non-blocking, allowing concurrent search operations during snapshot creation.

You can also manually trigger snapshots via the API, useful for backup and disaster recovery workflows. Snapshots are stored as compressed files and can be restored to rebuild a collection rapidly.

## HNSW Index and Approximate Nearest Neighbour

By default, Qdrant builds a Hierarchical Navigable Small World (HNSW) index over vector data. HNSW enables sublinear approximate nearest neighbor search—finding top-k similar vectors in logarithmic time rather than linear scans. The trade-off is approximation: HNSW may skip distant vectors at edges of clusters, but achieves recall above 95% in typical configurations.

Two key HNSW parameters control the index behavior:

**m** (number of bi-directional links) typically ranges from 4 to 64. Larger m increases memory overhead and index build time but improves recall. Default is 12.

**ef_construct** (construction parameter) affects accuracy during index building; typical values are 100–500. Larger values produce more accurate indices but slower indexing.

At query time, the **ef** parameter (search parameter) controls search thoroughness; larger ef yields higher recall but slower searches.

## Scroll API

For bulk retrieval and offline analytics, Qdrant provides the scroll API. Rather than paginating with offset/limit (inefficient for large datasets), scroll returns a cursor pointing to the next batch of points. Scroll operations stream points without recomputing the index, making them ideal for exporting collections, batch re-ranking, or iterating all points for embedding drift detection.

Scroll can apply filters and returns both vectors and payloads, allowing comprehensive offline analysis.
