# Retrieval-Augmented Generation (RAG)

Retrieval-Augmented Generation combines information retrieval with language model generation. Rather than relying on an LLM's training data alone, RAG systems retrieve relevant documents and provide them as context to the LLM, which generates answers grounded in the retrieved information. This significantly improves factuality, recency, and domain-specificity compared to closed-book question answering.

## RAG Pipeline Architecture

A canonical RAG pipeline has two stages:

**Retrieval:** Given a user query, retrieve the top-k most relevant documents from a knowledge base. This is typically implemented via vector similarity search or hybrid (dense + sparse) search. Retrieved documents are ranked and filtered.

**Generation:** The LLM is given the query and retrieved documents (called the context or supporting evidence), and generates an answer conditioned on this context. The LLM is explicitly instructed to cite retrieved documents and avoid hallucinating facts not in the context.

The quality of retrieval dominates the quality of generation. Even a sophisticated LLM cannot answer correctly if relevant documents are missing (retrieval miss). Conversely, a simple LLM can often generate a reasonable answer if given high-quality retrieved documents.

## Chunking Strategies

Documents must be broken into chunks before embedding and indexing. Chunking decisions profoundly affect retrieval quality.

**Fixed-size chunking** divides documents into overlapping windows of N tokens (e.g., 256 tokens). Simple to implement but may split semantic units awkwardly, cutting sentences mid-thought. Overlap (e.g., 50 tokens) ensures semantic continuity across chunk boundaries.

**Semantic chunking** uses sentence boundaries, paragraphs, or NLP-detected semantic breaks to divide content. More principled than fixed-size but requires NLP preprocessing and is slower.

**Tree-based chunking** hierarchically chunks documents: individual sentences at the finest level, paragraphs as medium chunks, entire documents at the coarsest level. At query time, a hierarchical reranker retrieves coarse chunks first, then fine-tunes with finer-grained chunks. This approach captures documents at multiple granularities, improving retrieval.

## Chunk Size and Overlap

**Chunk size** (typically 128–512 tokens) trades context richness against specificity:

- Small chunks (128 tokens): more specific, less context, many chunks per document
- Large chunks (512 tokens): more context, less specificity, fewer chunks per document

Small chunks are precise but may lack sufficient context for understanding. Large chunks provide context but can be noisy if documents are long and diverse.

**Overlap** (typically 0–100 tokens) ensures entities and concepts don't split across chunk boundaries. A 50-token overlap is common, balancing redundancy against semantic continuity.

The optimal chunk size is domain-specific. Legal documents often require 512+ tokens; technical documentation benefits from 256-token chunks.

## Retrieve-Then-Generate Pipeline

The most common RAG pattern: (1) embed the user query, (2) search for the top-k most similar documents from the index, (3) construct a prompt combining the query and retrieved documents, (4) call the LLM to generate an answer.

```
User Query → Embed → Vector Search → Retrieved Docs → Prompt → LLM → Answer
```

Retrieved documents are ranked by retrieval score and truncated to fit the LLM's context window. The top documents are included verbatim (or summarized for space efficiency).

Alternative patterns include **generate-then-retrieve** (LLM generates hypothetical answer, then retrieval searches for supporting docs) and **iterative retrieval** (LLM identifies missing information mid-generation, triggers additional retrievals).

## Grounding Answers in Retrieved Context

A critical aspect of RAG is ensuring the LLM's answer is grounded in retrieved documents, not hallucinated. System prompts typically include:

- "Answer only using the provided documents."
- "If the answer is not in the documents, say 'I don't know.'"
- "Cite specific documents when stating facts."

LLMs trained to follow instructions (e.g., via RLHF) generally comply with these directives, though some hallucination persists. Preference-trained models (like Claude, GPT-4) are more reliable at grounding than smaller open models.

Post-generation verification can check whether cited claims are actually present in retrieved documents, flagging unsupported assertions.

## Context Window Limits

LLMs have finite context windows (token limits). GPT-4 has 128K tokens; Claude Opus has 200K. Retrieved documents consume tokens, leaving space for the query and generated response.

A RAG system must respect this budget: if the knowledge base is huge and retrieval returns 1000 relevant documents, only the top 5–10 fit in context. This creates a strict dependency: retrieval quality is paramount. A single missed relevant document cannot be recovered at generation time.

Context window sizes vary across models and versions. RAG systems often aim to use 50% of the context for retrieved documents, reserving the rest for query and response.

## Citations and Source Attribution

High-quality RAG systems include citations: "According to document X, ...". This serves multiple purposes:

- Verifiability: users can check claims against sources
- Traceability: errors can be attributed to poor retrieval or poor summarization
- Transparency: users understand the LLM's reasoning

Citations can be generated by the LLM (asking it to cite documents in its response) or post-processed by checking whether generated claims appear in retrieved documents.

Hallucinated citations (citing a document that doesn't support the claim) are a failure mode. Preventing this requires careful prompt engineering and post-generation verification.

## RAG Failure Modes

**Retrieval miss:** Relevant documents are not retrieved. Causes include poor embedding models, mismatched query language (user says "what is the capital", but index contains "capital city"), or poor chunking strategies.

**Retrieval false positive:** Retrieved documents are irrelevant or contradictory. An LLM may over-weight early retrieved documents or synthesize contradictory sources incorrectly.

**Context truncation:** Retrieved documents are truncated to fit context windows, removing critical information.

**Hallucination:** LLM generates facts not supported by context. More common with smaller models and long context windows.

**Semantic mismatch:** Query and documents are embedded differently (different models, inconsistent preprocessing), leading to poor similarity scores.

## Why Retrieval Quality Dominates

End-to-end RAG quality is multiplicative: if retrieval finds the relevant document with 80% success and LLM generates a correct answer given that document with 95% success, end-to-end accuracy is 76% (0.8 × 0.95).

Improving retrieval from 80% to 95% improves end-to-end accuracy to 90% (0.95 × 0.95). Improving LLM accuracy from 95% to 99% improves end-to-end accuracy to only 79% (0.80 × 0.99).

This multiplicative property makes retrieval quality the dominant lever for improving RAG performance. Heavy investment in retrieval algorithms, re-ranking, and evaluation yields higher returns than chasing marginal LLM improvements.

## Evaluation and Iteration

RAG systems are evaluated on a ground-truth question set: pairs of (query, expected_answer, relevant_documents). Metrics include:

- **Hit@k:** Does retrieval return at least one relevant document in the top-k?
- **MRR (Mean Reciprocal Rank):** Average rank of the first relevant document
- **NDCG (Normalized Discounted Cumulative Gain):** Discounts ranked relevance, penalizing late-ranked relevant docs
- **End-to-end accuracy:** Does the LLM generate the correct answer given retrieved docs?

Systematic testing against these metrics, with segment-level analysis (e.g., performance by query type), identifies bottlenecks and guides optimization priorities.
