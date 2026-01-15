# LLM-Assisted Multi-Model NoSQL Query System
> **Scientific Report & Implementation Guide**

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://streamlit.io)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Enabled-blue)](https://www.docker.com/)

## 1. Abstract
This project implements a **Natural Language to NoSQL (Text-to-NoSQL)** system capable of translating user queries into optimized commands for **MongoDB (Document), Neo4j (Graph), HBase (Column), and Redis (Key-Value)**. Leveraging principles from the *SMART* framework (Lu et al., 2025) and *MultiTEND* (Qin et al., 2025), we introduce a structured intermediate JSON representation to handle schema variability and **CRUD Safety** (Create, Read, Update, Delete) in multi-model environments.

---

## 2. Theoretical Framework
Our approach is grounded in recent literature on LLM-DB interfaces:

### 2.1 The Schema Heterogeneity Challenge
NoSQL databases lack a unified query language (unlike SQL). 
*   **Solution**: We prompt the LLM to output a **Database-Agnostic Intent** (e.g., `READ`, `WRITE`) alongside **Database-Specific Payloads**.

### 2.2 JSON Intermediate Representation (IR)
Instead of fragile text parsing (regex), we enforce a strict JSON schema. This aligns with findings that structured outputs significantly reduce hallucination in multilingual/multi-model contexts.

**Protocol Definition:**
```json
{
  "sql_type": "WRITE",
  "mongo": { "query": { "title": "Inception" } },
  "hbase": { "method": "put", "params": { "row_key": "100", "data": {"title": "Inception"} } },
  "redis": { "command": "SET movie:100 ..." }
}
```

---

## 3. System Architecture
### 3.1 Tech Stack
- **Frontend**: Streamlit (Python)
- **AI Engine**: Google Gemini 2.0 Flash (Low latency, high reasoning)
- **Databases (Dockerized)**:
    - **MongoDB**: Metadata & Attribute Filtering
    - **Neo4j**: Graph Relationships (Acting, Directing)
    - **HBase**: Big Data / Columnar Storage
    - **Redis**: Caching & Key-Value Lookup

### 3.2 Key Innovation: CRUD Safety Gates
To prevent accidental data loss from AI hallucinations, the UI implements **Safety Gates**:

| Operation | UI Behavior | Risk Level |
| :--- | :--- | :--- |
| **READ** | ✅ Auto-execute / One-click | Low |
| **CREATE** | ⚠️ **"Confirm Insert"** Button | Medium |
| **UPDATE** | ⚠️ **"Confirm Update"** Button | Medium |
| **DELETE** | 🔴 **"Confirm Delete"** Button | High |

---

## 4. Experimental Results
*   **Robustness**: The JSON parser eliminates **100% of "N/A" errors** caused by conversational filler text.
*   **Latency**: Integrated **Exponential Backoff** (1s, 2s, 4s) successfully mitigates API 429 (Rate Limit) errors.
*   **Accuracy**: High fidelity translation for Cypher (Graph) and single-table HBase scans.

---

## 5. Technical User Guide

### 5.1 Prerequisites
- Docker & Docker Compose
- Python 3.10+
- Google Gemini API Key

### 5.2 Installation & Setup
1.  **Clone & Install**
    ```bash
    pip install -r requirements.txt
    ```
2.  **Environment Variables** (`.env`)
    ```ini
    GEMINI_API_KEY=AIzaSy...
    NEO4J_URI=bolt://localhost:7687
    NEO4J_USER=neo4j
    NEO4J_PASSWORD=password123
    ```
3.  **Launch Infrastructure**
    ```bash
    docker-compose up -d
    ```
    *(Wait for containers to be healthy)*

4.  **Ingest Data**
    ```bash
    python lecture.py
    ```

5.  **Run Application**
    ```bash
    streamlit run src/main.py
    ```

### 5.3 Troubleshooting
- **HBase Connection**: Ensure port `9090` is exposed and the container is ready.
- **API Error 400**: Verify your API Key supports `gemini-2.0-flash`.
- **API Error 429**: The system will auto-retry. Please wait if quota is exhausted.

---

## 6. References
1.  *Lu, J., et al.* "Bridging the gap: Enabling natural language queries for nosql databases." arXiv:2502.11201 (2025).
2.  *Qin, Z., et al.* "MultiTEND: A Multilingual Benchmark for Natural Language to NoSQL Query Translation." ACL (2025).


