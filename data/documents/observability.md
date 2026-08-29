# RAG and Machine Learning Observability

Observability is the practice of monitoring system health, performance, and data quality in production. For RAG and ML systems, observability goes beyond basic uptime monitoring to include data drift detection, retrieval quality assessment, and end-to-end accuracy tracking. Without observability, systems silently degrade as data distribution shifts or model performance drifts.

## Latency Metrics: Percentiles vs. Averages

Average latency is misleading. A system with median latency 50ms but occasional 5-second outliers may appear to have "100ms average latency" (misleading if tail latency dominates user experience).

**Percentile-based metrics** are more informative:

- **p50 (median):** 50% of requests complete in this time
- **p95 (95th percentile):** 95% of requests complete in this time; 5% are slower
- **p99 (99th percentile):** 99% of requests complete in this time; 1% are slower

For RAG systems, p95 and p99 matter more than p50 or average. A user waiting for the 99th-percentile request experiences that latency, not the average. Tracking p50/p95/p99 over time reveals whether optimization efforts reduced tail latency (hard problem) or median latency (easier).

SLA targets often specify p95 < 500ms, meaning at least 95% of requests complete within 500ms.

## Cache Hit Rate

Caches reduce latency and computation by storing previously computed results. **Cache hit rate** is the fraction of requests served from cache without recomputation.

```
Hit Rate = Hits / (Hits + Misses)
```

A RAG system might cache embeddings of frequently queried texts, or cache similarity search results for repeated queries. Monitoring hit rate reveals whether the cache is effective. A hit rate of 20% means 80% of requests incur full retrieval cost.

Hit rate depends on query distribution and cache size. Skewed query distributions (power-law: a few queries are repeated frequently) achieve high hit rates with small caches. Uniform distributions require large caches or are unsuitable for caching.

## Retrieval Evaluation Metrics

Retrieval quality is central to RAG. Standard information-retrieval metrics quantify retrieval performance:

**Hit@k (Hits at k):** For a given query, if at least one relevant document is in the top-k retrieved results, the query "hits". Hit@10 is typical; it measures recall at a fixed cutoff.

**MRR (Mean Reciprocal Rank):** For each query, compute the reciprocal of the rank of the first relevant document. Average across queries. MRR=0.5 means the first relevant result is on average at rank 2.

**Recall@k:** What fraction of all relevant documents are in the top-k results? Recall@10=0.8 means 80% of relevant documents appear in the top-10. Recall is important for comprehensiveness but computationally expensive to compute (requires knowing all relevant documents).

**NDCG (Normalized Discounted Cumulative Gain):** Discounts ranked relevance: a relevant document at rank 1 is worth more than one at rank 10. Normalizes against perfect ranking. Range 0–1; higher is better.

These metrics are computed against a ground-truth evaluation set: questions annotated with relevant documents by domain experts. Without ground truth, retrieval quality is invisible.

## Ground-Truth Question Sets

Creating evaluation sets requires human annotation. Domain experts review a sample of queries (typically 100–1000), identify relevant documents for each query, and create a labeled dataset.

This ground-truth set enables benchmark evaluation: retrieval and end-to-end metrics can be computed reproducibly. New systems are compared against baselines on this fixed evaluation set.

Ground-truth sets should be representative of production queries but also include edge cases, rare queries, and adversarial cases (queries designed to test specific system components).

## Embedding Drift Detection

Embedding models change over time. Model updates, training data shifts, or data preprocessing changes alter vector representations. Old embeddings (computed with v1.4 of a model) are no longer compatible with new embeddings (computed with v1.5).

**Centroid embedding** is the mean of all embeddings in a collection:

```
centroid = mean([embedding_1, embedding_2, ..., embedding_N])
```

Monitor the centroid over time. Compute cosine distance between today's centroid and yesterday's centroid. If the distance exceeds a threshold (e.g., 0.05), embedding drift is detected.

Centroid drift indicates distribution shifts: either the data being indexed has changed, or the embedding model has updated. Detection triggers re-indexing: re-embedding all documents with the new model to maintain index consistency.

## Re-indexing Triggers

Re-indexing is expensive: re-embedding millions of documents takes hours. Triggers determine when re-indexing is necessary:

**Time-based:** Re-index weekly or monthly, regardless of drift detection. Simple but may re-index unnecessarily or miss urgent drift.

**Drift-based:** Re-index when embedding centroid drift exceeds a threshold (e.g., cosine distance > 0.05). Principled but requires monitoring.

**Model-version-based:** Re-index when the embedding model is updated (e.g., upgrading from bge-small v1.4 to v1.5). Explicit and straightforward.

**Quality-based:** Re-index when end-to-end RAG accuracy drops below a threshold (e.g., Hit@10 < 0.85). Reactive but directly measures impact.

A hybrid approach combines multiple triggers: re-index on model updates or significant drift, and do a full re-index monthly as a safeguard.

## Production Monitoring and Alerting

Key metrics to monitor continuously in production:

- **Request latency** (p50/p95/p99): Early warning of performance degradation
- **Error rates**: Exceptions, timeouts, model inference failures
- **Cache hit rate**: Indicates whether caching is effective
- **Retrieval Hit@10**: Sampled on production queries to detect retrieval quality drift
- **Embedding centroid drift**: Triggers re-indexing when significant

Alerting rules trigger notifications when metrics exceed thresholds. Examples:

- p95 latency > 500ms → investigate performance
- Hit@10 < 0.80 → investigate retrieval quality or data drift
- Error rate > 1% → investigate system health
- Embedding centroid drift > 0.05 → schedule re-indexing

Dashboards visualize metrics over time, enabling trend analysis and root-cause investigation.

## Logging and Tracing

Every request should be logged with:

- Request ID (for cross-service tracing)
- Query
- Retrieved documents (IDs and scores)
- Generated answer
- Latency breakdown (retrieval time, LLM time, etc.)
- User/session ID (for A/B testing and segmentation)

Structured logs enable filtering and analysis: "What is the average Hit@10 for queries with latency > 1000ms?" Traces correlate latencies across components, identifying bottlenecks.

For RAG systems, detailed logs enable post-mortem analysis: given a query where the LLM's answer was incorrect, logs reveal whether retrieval missed relevant documents or the LLM misunderstood the context.

## Segment-Level Analysis

Aggregate metrics can mask problems in subpopulations. Segment-level analysis breaks metrics by query type, document category, user segment, etc.

Example: overall Hit@10 is 0.90, but for queries about "embeddings", Hit@10 is 0.70. This signals a domain-specific problem (perhaps insufficient documentation on embeddings) that global metrics missed.

Segmentation enables targeted improvement: focus re-indexing or re-training on low-performing segments before attempting global optimization.

## Cost and Value Tracking

ML systems incur direct costs: model inference (API calls or compute), vector database storage, and retrieval latency (user time). Track cost per request and cost per correct answer.

If improving retrieval recall from 0.90 to 0.95 requires re-encoding all 10 million documents (1-hour cost: $10), but increases revenue by $100/month, the ROI is positive. Metric tracking enables cost-benefit analysis for optimization decisions.

Observability without action is waste. Use metrics to identify high-impact improvements, measure their effect, and iterate.
