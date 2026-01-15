# Literature Review: LLM-Assisted Query Generation for NoSQL Databases

## 1. Abstract & Introduction
The proliferation of NoSQL databases (Document, Graph, Key-Value, Columnar) has created a significant barrier for non-technical users due to lack of a unified query language like SQL. While "Text-to-SQL" is a mature field, "Text-to-NoSQL" remains under-explored. This review analyzes recent literature provided for this project, highlighting the gap between relational and non-relational NLQ systems. Key challenges identified include schema heterogeneity, the lack of standard benchmarks, and the necessity for execution-aware validation to prevent hallucinations in schemaless environments.

## 2. Paper Summaries

### 2.1 MultiTEND: A Multilingual Benchmark for Natural Language to NoSQL (Qin et al., 2025)
- **Problem**: Existing NLQ systems focus on English and Relational DBs. NoSQL lacks multilingual support.
- **Method**: Introduces **MultiLink**, a framework using a "Parallel Linking Process" to map multilingual intents to NoSQL operators. It decomposes the task into:
    1. Multilingual NoSQL Sketch Generation (Operator mapping).
    2. Monolingual Schema Linking (Entity mapping).
- **Dataset**: **MultiTEND**, covering 6 languages (En, De, Fr, Ru, Ja, Zh) and 4 NoSQL types.
- **Key Findings**:
    - "Structural Challenge": Syntactic differences across languages hinder operator mapping.
    - "Lexical Challenge": Schema linking is harder in multilingual contexts (e.g., morphology).
    - MultiLink improves execution accuracy by ~15% over baselines.

### 2.2 Bridging the Gap: The SMART Framework (Lu et al., 2025)
- **Problem**: Direct "Text-to-NoSQL" translation is fragile due to complex nested structures and API variability.
- **Method**: Proposes **SMART** (SLM-assisted, Multi-step, Augmented, RAG, Translation):
    - **Step 1**: Schema Prediction (SLM predicts used fields).
    - **Step 2**: RAG (Retrieve similar (NLQ, Query) pairs).
    - **Step 3**: Draft Generation (SLM/LLM generates initial query).
    - **Step 4**: **Execution-based Refinement** (Execute query; if fails/empty, feed error back to LLM to fix).
- **Dataset**: **TEND** (Text-to-NoSQL Dataset), constructed semi-automatically from Spider (SQL) dataset.
- **Key Findings**:
    - Rules/Grammar-based conversion fails (10% accuracy).
    - LLM + RAG + Execution Loop achieves ~65% accuracy.
    - **Execution Feedback** is critical for debugging non-standard NoSQL queries.

### 2.3 LLM-Enhanced Data Management in Multi-Model Databases (Yang, 2025 - Master's Thesis)
- **Problem**: Managing diverse data models (MMDBs) is complex. LLMs can assist but face risks.
- **Scope**: Survey of LLM applications in MMDBs: Querying, Integration, Optimization, Privacy.
- **Key Constraints**:
    - **Hallucination**: LLMs may invent non-existent fields (risky in schemaless DBs).
    - **Privacy**: Sending private data to LLM APIs is a concern.
    - **Security**: "Prompt Injection" could lead to unauthorized data access.
- **Recommendations**: Use "Safe-by-design" architectures (Validation layers, Human-in-the-loop).

### 2.4 Natural Language Query Engine for Relational Databases (Tueno, 2024)
- **Problem**: SQL complexity for non-experts.
- **Focus**: Relational DBs (SQL).
- **Key Insight**: Emphasizes **Response Generation**—it's not enough to return raw rows; the system must explain the answer in natural language.
- **Relevance**: While SQL-focused, the architecture (NLQ -> Validation -> Query -> Response) establishes the baseline requirement for user-friendly output.

## 3. Cross-Paper Synthesis

### Shared Bottlenecks
1.  **Schema Linking**: All papers agree that identifying the correct collection/table and field names is the #1 failure mode, especially in NoSQL where schemas are flexible.
2.  **Ambiguity**: Users don't specify the "variant" of the NoSQL query (e.g., Mongo Aggregation vs Find).
3.  **Safety**: Yang (2025) and Lu (2025) both imply that *execution* is needed for validation, but executing arbitrary LLM-generated code is unsafe without "Safety Gates".

### Why Multi-Step > Single-Shot
Lu et al. (SMART) prove that single-shot generation fails (10-40% accuracy) because the LLM hallucinates API syntax. A multi-step pipeline (Schema -> Draft -> Refine) forces the model to "ground" itself in the actual database metadata before writing code.

## 4. Research Claims & Requirements Mapping

| Claim | Source | System Requirement |
| :--- | :--- | :--- |
| "Execution feedback improves accuracy by ~15%" | Lu et al. (2025) | Implement **Module E (Refinement Loop)**: Retry query on error. |
| "Schema heterogeneity requires structural IR" | Qin et al. (2025) | Implement **Module C (IR)**: Use JSON intermediate format before DB-specific query. |
| "Hallucination is a primary risk in MMDBs" | Yang (2025) | Implement **Module D (Validation)**: Policy checks and Schema validation. |
| "Natural language response is key for UX" | Tueno (2024) | Implement **Module A (Explain)**: Convert results back to NL summary. |

## 5. References
1.  Qin, Z., et al. (2025). *MultiTEND: A Multilingual Benchmark for Natural Language to NoSQL Query Translation*. arXiv:2502.11022.
2.  Lu, J., et al. (2025). *Bridging the gap: Enabling natural language queries for nosql databases*. arXiv:2502.11201.
3.  Yang, T. (2025). *LLM-Enhanced Data Management in Multi-Model Databases*. Master's Thesis, University of Helsinki.
4.  Tueno, S. (2024). *Natural Language Query Engine for Relational Databases using Generative AI*. arXiv:2410.07144.
