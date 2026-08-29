# Vector Search and Similarity Retrieval

Vector search, also known as semantic search or similarity search, is the process of finding vectors nearest to a query vector in high-dimensional space. It powers modern retrieval systems by enabling semantic matching without explicit keyword indexing. Understanding vector search algorithms, distance metrics, and the recall-latency tradeoff is critical for building efficient RAG systems.

## Nearest-Neighbor Search Fundamentals

At its core, vector search answers the question: "Which vectors in my collection are most similar to this query vector?" Similarity is quantified by a distance metric. A brute-force approach computes distances from the query to every indexed vector, identifies the top-k closest, and returns them. Brute-force is exact but O(n) in complexity, infeasible for collections exceeding millions of vectors.

The top-k retrieval task is well-defined: return the k vectors with the smallest (or largest, depending on metric) distance scores. For k=10, you retrieve the 10 nearest neighbors.

## Approximate Nearest Neighbor (ANN)

Approximate nearest neighbor algorithms trade exactness for speed. Instead of computing all distances, they use data structures and heuristics to prune the search space, achieving sublinear query time at the cost of potentially missing the true nearest neighbors.

The key metric is **recall**: the fraction of true top-k neighbors found by the approximation. A recall of 0.95 means 95% of the true top-10 results were found. Recall is measured against a ground-truth baseline (brute-force exact search).

ANN algorithms differ in construction cost, query speed, and recall. Most modern systems achieve 90–99% recall at practical query latencies.

## HNSW (Hierarchical Navigable Small World)

HNSW is a graph-based ANN algorithm organized in layers. At the bottom layer, every point is connected to its nearest neighbors. Higher layers form successively sparser graphs, enabling fast navigation.

During search, the algorithm starts at the top layer's entry point and greedily navigates to closer neighbors, progressively descending layers. This hierarchical organization achieves logarithmic complexity: navigating 1 million vectors requires only ~log(1M) ≈ 20 distance computations.

HNSW is memory-efficient and supports efficient incremental insertions. Qdrant and other production vector databases default to HNSW for these reasons.

## IVF (Inverted File)

IVF divides the vector space into clusters using k-means. Each query is compared against cluster centers, retrieving only vectors from promising clusters, not the entire dataset.

IVF is faster than HNSW for very large datasets but requires clustering preprocessing. It scales linearly with the number of clusters (nprobe), whereas HNSW's graph navigation is logarithmic. IVF works well when cluster separation is clear; degrades when clusters overlap significantly.

## Recall vs. Latency Tradeoff

ANN algorithms expose parameters controlling the recall-latency tradeoff. In HNSW, the search parameter (ef) controls how many neighbors to explore per layer. Larger ef yields higher recall but slower searches. In IVF, nprobe (number of clusters to search) controls the tradeoff.

RAG systems must balance quality and speed: missing relevant documents (low recall) harms answer quality, but slow searches hurt user experience. A typical target is 90–95% recall, accepting that 1 in 10 relevant documents might be missed in exchange for 10–50ms query latency.

## Distance Metrics

**Cosine Distance** measures the angle between vectors. It ranges from 0 (identical) to 2 (opposite) for normalized vectors. Cosine distance is invariant to magnitude, so normalized embeddings from sentence-transformers have identical cosine similarity regardless of scale. Most common for semantic search.

**Dot Product** is the raw inner product, proportional to cosine similarity for normalized vectors. It is computationally cheaper than explicit cosine distance (no normalization needed at query time if vectors are pre-normalized). Often used interchangeably with cosine for normalized embeddings.

**Euclidean Distance** is the L2 norm, the straight-line distance in vector space. It is sensitive to magnitude and generally slower in high dimensions. Used less frequently in RAG but sometimes in specialized applications (e.g., some clustering algorithms).

The choice of metric affects not just retrieval quality but also index construction and search performance. Cosine and dot product are preferred for text embeddings.

## Top-k Retrieval and Result Ranking

Top-k retrieval returns the k nearest neighbors. In RAG, k is typically 5–20, balancing context relevance with token budget (fitting retrieved documents in the LLM's context window).

Results are ranked by distance score by default. However, ANN can miss true neighbors, so retrieved results may include false positives (high-distance, low-relevance vectors) while missing true positives (true neighbors below the top-k boundary).

## Re-ranking

Re-ranking is a post-processing step that improves retrieval quality: after retrieving top-k from the ANN index, a more expensive but accurate model re-scores and re-ranks these candidates.

Common re-ranking strategies include:

- **Cross-encoder rerankers**: neural models trained to score query-document pairs directly (e.g., BAAI/bge-reranker-v2-m3).
- **LLM reranking**: asking an LLM to rate retrieved documents' relevance.
- **Diversity reranking**: spreading results across topics to reduce redundancy.

Re-ranking is computationally heavier than initial retrieval but applied only to top-k candidates, making it practical. It often recovers missed relevant documents and removes false positives, improving end-to-end RAG quality.

## Hybrid Search

Hybrid search combines dense (vector) and sparse (keyword/BM25) retrieval. A query generates both embeddings (semantic) and BM25 scores (keyword matching), and results from both are merged.

**BM25** is a classical ranking function that scores documents based on keyword frequency and inverse document frequency. It excels at exact-match queries and rare terms.

**Dense retrieval** captures semantic similarity.

Hybrid search is more robust than dense-only: if exact keywords matter (e.g., "Python 3.11 release date"), BM25 ensures those documents rank high. If semantic meaning matters (e.g., "embedding models"), dense vectors dominate. Weighting the two branches (e.g., 0.5 * dense_score + 0.5 * bm25_score) balances the approaches.

Modern vector databases support both dense and sparse indices, enabling efficient hybrid search in a single query.
