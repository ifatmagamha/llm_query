# LLM-Assisted Multi-Model NoSQL Query System

> **Scientific Report & Implementation Guide**

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://streamlit.io)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Enabled-blue)](https://www.docker.com/)

## Abstract
This project implements a **Natural Language to NoSQL (Text-to-NoSQL)** system capable of translating user queries into optimized commands for **MongoDB (Document), Neo4j (Graph), HBase (Column), and Redis (Key-Value)**. Leveraging principles from the *SMART* framework (Lu et al., 2025) and *MultiTEND* (Qin et al., 2025), we introduce a structured intermediate JSON representation to handle schema variability and **CRUD Safety** (Create, Read, Update, Delete) in multi-model environments.

---

## Overview
This project implements a **Research-Grade "Text-to-NoSQL" System** enabling natural language interaction with **MongoDB**, **Redis**, **Neo4j**, **HBase**, and **RDF**.

It utilizes the **SMART-lite** framework (**S**chema **M**atching, **A**ugmented, **R**efined **T**ranslation) to ensure high accuracy and safety when generating queries for non-relational databases.

## 🚀 Features
*   **Polyglot Persistence**: Seamlessly queries Document, Graph, Key-Value, Columnar, and Semantic stores.
*   **Parallel Execution Engine**: Uses `ThreadPoolExecutor` to query all 5 databases simultaneously in Cross-DB mode.
*   **Safety-First**: `PolicyValidator` acts as a firewall, blocking adversarial mutations (`DROP`, `FLUSHALL`) even if the LLM generates them.
*   **Self-Healing**: Execution feedback loop corrects syntax errors automatically.
*   **LLMOps Ready**: Includes automated benchmarks, logging, and comprehensive audit reports.

## 📦 Installation

1.  **Clone & Install**
    ```bash
    git clone <repo_url>
    cd llm_query
    pip install -r requirements.txt
    ```

2.  **Environment Setup**
    Create a `.env` file:
    ```ini
    GEMINI_API_KEY=your_google_api_key_here
    ```

3.  **Start Databases** (Docker)
    ```bash
    docker-compose up -d
    ```

4.  **Load Sample Data**
    ```bash
    # (Optional) Load sample data into Mongo/Neo4j/Redis
    python lecture.py
    ```

## 🖥️ How to Run

### 1. Interactive Web UI (Streamlit)
The best way to explore the system.
```bash
streamlit run src/main.py
```
*   Select your target DB from the sidebar.
*   Type questions like "Who directed Inception?"
*   View the internal "Thinking Process" (IR generation).

### 2. Command Line Interface (CLI)
For quick testing or headless operation.

**Syntax:**
```bash
python src/cli.py --db <TYPE> --query "<QUESTION>" [--details] [--unsafe]
```

**Examples:**
*   **MongoDB**: `python src/cli.py --db mongo --query "Find action movies rated > 8"`
*   **Neo4j**: `python src/cli.py --db neo4j --query "Who acted in The Matrix?"`
### 3. Comprehensive System Audit
Run the exhaustive test suite covering Deep Dive, Cross-DB, and Safety scenarios:
```bash
python tests/comprehensive_test.py
```
*   HTML/Markdown Report saved to: `reports/comprehensive_test_report.md`

## 📊 Benchmarking & LLMOps
Generate a performance report measuring Latency and Accuracy across 5 test scenarios.

```bash
python tests/benchmark.py
```
*   Report saved to: `reports/benchmark_report.md`

## 📂 Project Structure
*   `src/connectors/`: Drivers for Mongo, Redis, Neo4j, HBase, RDF.
*   `src/pipeline/`: Logic for RAG, Hallucination Check, and Execution Loop.
*   `src/ir/`: JSON definitions for Abstract Query Intent.
*   `src/optimization/`: Scripts for Auto-Indexing.

## 🎯 Objectives Achieved (University Requirements)
1.  **Natural Language Query Translation**: Supports 5 paradigms (Document, Graph, Key-Value, Column, Semantic).
2.  **Database Schema Exploration**: "Schema Explorer" in UI fetches real-time metadata (Collections, Labels, Keys).
3.  **Query Validation**: `PolicyValidator` implements "Safe-by-Default" (blocks `DELETE`/`DROP`).
4.  **Cross-Database Comparison**: Dedicated UI mode to compare how one NLQ translates to MongoDB vs Neo4j vs RDF.
5.  **Research-Based**: Implements logic from *MultiTEND* (2025) and *SMART* (2025) papers.

## 🔮 Future Perspectives
Based on our literature review, future iterations could include:
*   **Fine-Tuned Models**: Training Llama-3 specifically on NoSQL dialects instead of using generic LLMs.
*   **Vector Search**: Integrating Vector Embeddings (RAG) directly into MongoDB/Redis for semantic caching.
*   **Multi-Turn Context**: Maintaining conversational state ("Who directed it?" referring to previous result).

## 📜 Research References
*   *MultiTEND: A Multilingual Benchmark for Natural Language to NoSQL Query Translation* (Qin et al., ACL 2025)
*   *Bridging the Gap: Enabling Natural Language Queries for NoSQL Databases* (Lu et al., arXiv 2025)

