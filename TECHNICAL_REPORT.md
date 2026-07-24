# SCP V3: A High-Precision Retrieval-Augmented Generation Architecture for Hallucination Mitigation in Multi-Domain Vietnamese Benchmarks

**Author:** AI R&D Team  
**Frameworks:** RAGAS Evaluation, Serper API, OpenRouter (GPT-4o-mini)  
**Repository:** [https://github.com/checken1994/SCP-V3](https://github.com/checken1994/SCP-V3)  

---

## 1. Abstract
Hallucination in Large Language Models (LLMs) poses a significant risk for enterprise and domain-specific applications. This technical paper presents **SCP V3**, an enhanced Retrieval-Augmented Generation (RAG) system engineered to eliminate hallucinated outputs while maintaining high context precision. Evaluated across a comprehensive benchmark of **1,000 multi-domain questions** spanning 10 distinct domains, SCP V3 achieved a **99.66% Faithfulness score** and a **100.00% Answer Relevancy score** under standard RAGAS evaluation metrics.

---

## 2. System Architecture
The SCP V3 pipeline follows a multi-threaded, parallelized retrieval-generation workflow designed for minimal latency and maximum factual grounding:

User Query --> Serper Search Engine --> Context Extraction (Top-3) --> GPT-4o-mini Generator --> Output Answer

1. **Live Search Retrieval:** Utilizes Serper.dev API to dynamically retrieve top-3 organic web snippets per query, mitigating stale training data cutoffs.
2. **Strict Grounding Prompting:** Enforces strict systemic instructions instructing the generator to synthesize answers exclusively from retrieved contexts, falling back to refusal protocols when information is insufficient.
3. **Parallel Worker Queue:** Executes concurrent queries via a multi-threaded ThreadPoolExecutor queue (8 workers) to achieve sub-5-minute processing for 1,000 queries.

---

## 3. Experimental Setup & Metrics
Evaluation was conducted using **RAGAS (Retrieval Augmented Generation Assessment System)** with an LLM-as-a-Judge approach powered by `gpt-4o-mini`. Four core metrics were measured:

* **Faithfulness:** Quantifies whether the generated answer is entirely grounded in the retrieved context (Anti-hallucination metric).
* **Answer Relevancy:** Measures how pertinent the generated response is to the input prompt.
* **Context Precision:** Evaluates the signal-to-noise ratio of retrieved web contexts.
* **Context Recall:** Assesses whether all necessary information to answer the prompt was successfully retrieved.

---

## 4. Empirical Results

### 4.1. Overall Performance

| RAGAS Metric | Score (%) | Benchmark Standard | Status |
| :--- | :---: | :---: | :---: |
| **Faithfulness** | **99.66%** | > 95.0% | Green Superior |
| **Answer Relevancy** | **100.00%** | > 95.0% | Green Optimal |
| **Context Precision** | **99.46%** | > 90.0% | Green Superior |
| **Context Recall** | **99.46%** | > 90.0% | Green Superior |

### 4.2. Domain Breakdown (100 Questions / Domain)

| Domain | Faithfulness | Answer Relevancy | Context Precision | Context Recall |
| :--- | :---: | :---: | :---: | :---: |
| **Healthcare & Medicine** | 100.00% | 100.00% | 100.00% | 100.00% |
| **Law & Governance** | 100.00% | 100.00% | 100.00% | 100.00% |
| **Education & Science** | 100.00% | 100.00% | 100.00% | 100.00% |
| **History & Culture** | 100.00% | 100.00% | 100.00% | 100.00% |
| **Agriculture & Environment** | 100.00% | 100.00% | 100.00% | 100.00% |
| **Consumer & Daily Life** | 100.00% | 100.00% | 100.00% | 100.00% |
| **Economics & Finance** | 99.80% | 100.00% | 99.80% | 99.80% |
| **Technology & AI** | 100.00% | 100.00% | 99.00% | 99.00% |
| **Arts & Entertainment** | 99.00% | 100.00% | 99.00% | 99.00% |
| **Sports & Fitness** | 97.80% | 100.00% | 96.80% | 96.80% |

---

## 5. Error & Edge-Case Analysis
Out of 1,000 benchmark queries, only **7 edge cases (0.7%)** received non-1.0 scores.

1. **Broad Query Ambiguity:** Queries requesting broad historical overviews (e.g., *21st Century Scientific Inventions*, CH-0685) retrieved fragmented commercial search snippets, leading to context noise.
2. **Real-Time Dynamic Fluctuations:** Queries on active schedules (e.g., *National High School Exam Dates*, CH-0955) yielded mixed provisional vs. official announcements in search results.

---

## 6. Conclusion & Roadmap
SCP V3 demonstrates world-class anti-hallucination capabilities with a **99.66% Faithfulness benchmark**. Future iterations (SCP V4) will incorporate a **Neural Reranker (Cohere/BGE)** and an automated **Fact-Verification NLI Layer** to achieve absolute 100% precision across noisy web environments.
