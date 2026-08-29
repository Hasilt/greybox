# Text Embeddings and Vector Representations

Text embeddings are dense vector representations that encode semantic meaning of text into fixed-dimensional space. An embedding model transforms text into a vector, enabling similarity comparisons and vector-space operations. Modern embeddings are the foundation of semantic search and RAG systems.

## Dense Vector Representation

An embedding is a vector of floating-point numbers, typically between 64 and 1536 dimensions depending on the model. Each dimension captures some learned semantic feature. Unlike sparse representations (word counts, TF-IDF), dense vectors are learned end-to-end via neural networks, capturing subtle semantic relationships.

Semantically similar texts produce embeddings with high cosine similarity. The relationship is learned during pre-training: models see millions of text pairs and learn to place similar texts near each other in embedding space.

Dense embeddings enable efficient retrieval via vector similarity search. Once indexed, queries are answered in milliseconds using approximate nearest neighbor algorithms, making real-time semantic search practical.

## Sentence-Transformers Architecture

Sentence-Transformers (transformers library's `sentence-transformers` package) are BERT-based models fine-tuned for embedding entire sentences and documents. Unlike raw BERT (which produces token-level embeddings), sentence-transformers apply pooling (typically mean pooling over token embeddings) to generate a single sentence-level vector.

Sentence-transformers are trained on sentence pairs, learning to maximize similarity between semantically related pairs and minimize it for unrelated pairs. This training objective is more suited to semantic search than BERT's masked language modeling objective.

The architecture supports both CPU and GPU inference, with batch processing for throughput. Model sizes range from 22M parameters (all-MiniLM) to 435M parameters (all-mpnet-base), trading quality against latency.

## BAAI/bge-small-en-v1.5 Model

The BAAI/bge-small-en-v1.5 model is a state-of-the-art sentence-transformer optimized for English retrieval. BAAI (Beijing Academy of Artificial Intelligence) trained it on diverse datasets including real user queries and web documents.

**Key specifications:**
- **Embedding dimensionality: 384** (fixed)
- **Parameter count: ~33M** (small compared to base models)
- **Input length: up to 512 tokens** (covers most documents and queries)
- **Trained on:** diverse retrieval datasets including MS MARCO, Natural Questions, and web data
- **Output normalization:** produces L2-normalized vectors (unit norm)

The 384-dimensional output is a sweet spot: sufficient expressiveness for fine-grained semantic distinctions, low enough to index millions of vectors efficiently. Normalized vectors are ideal for cosine similarity, the standard metric for semantic search.

The model excels at both query and document encoding. It can encode short queries and long documents uniformly, making it suitable for end-to-end RAG pipelines.

## Embedding Dimensionality and Efficiency

Embedding dimensionality affects memory, computation, and index performance. Higher dimensions capture more semantic nuance but require more memory and computation per vector.

A 1-million-vector index with bge-small (384 dims) consumes ~1.5 GB in memory with uint8 quantization, ~3 GB with float32. Conversely, larger models (768+ dims) may exceed memory budgets on modest hardware.

Dimensionality reduction techniques (PCA, UMAP) can compress embeddings to lower dimensions, reducing memory and latency at the cost of quality loss. Empirically, compressing from 384 to 256 dims typically causes 1–5% recall degradation.

## Normalization for Cosine Similarity

Cosine similarity measures the angle between vectors: `cos_sim = (u · v) / (||u|| * ||v||)`. For normalized vectors (unit L2 norm), the formula simplifies to `cos_sim = u · v` (dot product), eliminating the normalization step.

Sentence-transformers and bge-small output L2-normalized vectors by default. When indexed in vector databases like Qdrant with cosine distance, this normalization is already applied, ensuring optimal speed.

If using dot-product distance, vectors must be pre-normalized. If using unnormalized embeddings, cosine distance is required to account for magnitude differences.

## Query vs. Passage Encoding

A subtle but important aspect of embeddings is that the same model can encode both queries (typically short) and passages (potentially long). Queries and passages are semantically different—a query like "what is RAG" should be embedded to be similar to passages containing the answer.

Some models fine-tune query and passage encoders separately (e.g., DPR, ColBERT), producing different embeddings for the same text depending on whether it's a query or passage. Bge-small uses a single encoder but is trained on query-passage pairs, learning to place queries and relevant passages near each other.

For maximum accuracy, use query-specific encoders if available. For simplicity, a unified model like bge-small is practical and effective for most RAG applications.

## Semantic Similarity and Clustering

Embeddings enable semantic clustering: computing similarity between all pairs, grouping similar vectors. This is useful for topic modeling, duplicate detection, and organizing document collections.

Semantic similarity is correlation-agnostic: embedding vectors capture meaning, not just surface keywords. "The car is red" and "A red automobile" are close in embedding space despite different word order. This robustness is why embeddings outperform keyword search for understanding intent.

## Batching and Inference Optimization

Encoding large document collections efficiently requires batching. Sentence-transformers support mini-batch encoding, processing multiple documents in parallel on GPU. Typical batch sizes are 32–256 depending on document length and hardware.

Batching amortizes model initialization and GPU allocation overhead, reducing per-document encoding cost from milliseconds to microseconds. For encoding 1 million documents, proper batching (vs. one-by-one encoding) can reduce total time from hours to minutes.

Libraries like InfiniBatch and vLLM further optimize encoding throughput.

## Embedding Drift and Model Versioning

Embedding models improve over time. Upgrading from bge-small-en-v1.4 to v1.5 changes vector representations slightly. Old embeddings (encoded with v1.4) are no longer comparable to new embeddings (encoded with v1.5) in the same index.

**Embedding drift detection** monitors the centroid (mean) embedding of recent documents. If the centroid embedding shifts significantly (measured by cosine distance to the previous centroid), it signals that data distribution or model has changed, requiring re-indexing.

In production, storing the embedding model version with each index and monitoring centroid drift enables timely re-indexing and prevents relevance degradation.

## Challenges and Best Practices

Embeddings are not perfect: they can conflate unrelated concepts, miss subtle distinctions, and degrade on out-of-distribution text. Best practices include:

- Using embeddings trained on retrieval data (like bge) rather than generic pretrained embeddings (plain BERT).
- Normalizing input text consistently (lowercasing, removing special characters).
- Re-embedding periodically as models improve.
- Using re-ranking to recover from embedding limitations.
- Testing on domain-specific evaluation sets to catch drift early.
