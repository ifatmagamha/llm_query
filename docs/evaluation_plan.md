# Evaluation Plan: Text-to-NoSQL Research

## 1. Objectives
To assess the effectiveness of the **Polyglot Persistence** architecture and **SMART-lite** pipeline in handling multi-model query generation.

## 2. Methodology

### 2.1 Datasets
We will use two datasets:
1.  **Synthetic Benchmark (Internal)**: 50 generic questions (Find, Count, Aggregate) manually translated to Mongo, Cypher, Redis, and SPARQL.
2.  **MultiTEND Subset**: A subset of the Multi-lingual benchmarks translated to our specific schema.

### 2.2 Metrics
We follow the TEND paper metrics (Lu et al., 2025):
-   **Execution Accuracy (EX)**: Does the generated query return the same result set as the Gold Query? (Primary Metric)
-   **Valid Syntax (VS)**: Is the query parseable by the engine?
-   **Safety Violation Rate (SVR)**: Percentage of unsafe queries (e.g., DROP) blocked by the policy layer.

### 2.3 Ablation Studies
We will run the following configurations to isolate component contributions:
1.  **Baseline (Zero-Shot)**: Prompt LLM directly with "Write a Mongo query for...". No RAG.
2.  **Schema-Only**: Provide schema metadata but no RAG examples.
3.  **RAG**: Provide similar examples (Current Pipeline).
4.  **Full Pipeline (SMART-lite)**: RAG + **Execution Feedback Loop**.

## 3. Experimental Setup (Automated)

### Test Runner
A script `tests/benchmark.py` will:
1.  Load questions from `data/benchmark.json`.
2.  Run each question through the 4 configurations.
3.  Execute against a "Gold" Docker environment.
4.  Compare results.

### Failure Analysis Categories
We will manually tag failures as:
-   **Schema Hallucination**: Inventing fields.
-   **Syntax Error**: Invalid braces/keywords.
-   **Semantic Error**: Correct syntax, wrong intent (e.g., OR vs AND).
-   **Unsupported Feature**: e.g., using a Mongo operator not available in version X.

## 4. Expected Outcomes
-   **Hypothesis 1**: Graph queries (Neo4j) will show the highest improvement from RAG due to complex Cypher syntax.
-   **Hypothesis 2**: Smart-lite (feedback loop) will resolve ~20% of Syntax Errors.
