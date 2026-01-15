# Project Evolution & Design Rationale

This document tracks the iterative development of the "LLM-Assisted Query Generation" system, documenting how "perceptions" and research goals have drove architectural changes.

## Version 1: The "Streamlit Demo" (Initial Perception)
**Goal**: fast prototyping of a UI that "talks" to a database.
- **Architecture**: Monolithic `main.py` containing UI, prompt logic, and DB connection strings.
- **Data Model**: Ad-hoc. Just enough data to make the demo work.
- **Approach**: Direct "Text-to-Query" (Zero-shot).
- **Limitation**:
    - **Fragile**: Complex queries failed often.
    - **Unsafe**: No difference between "Find movies" and "Delete movies".
    - **Unscalable**: Adding a new DB meant rewriting `main.py`.

---

## Version 2: The "Research Prototype" (Current Perception)
**Goal**: A scientifically rigorous system to *evaluate* Text-to-NoSQL capabilities across paradigms.
**Driver**: Insights from literature (MultiTEND, SMART framework) revealed that "Zero-shot" is insufficient for NoSQL's schema complexity.

### Key Shifts:

#### 1. From Monolithic to Modular
- **Why**: We need to test *just* the "IR Generation" or *just* the "Connector" logic independently.
- **Change**: Split `src/` into `connectors/`, `ir/`, `pipeline/`.

#### 2. From Single-Schema to Polyglot Persistence
- **Perception**: "Is MongoDB better than Neo4j for this?"
- **Change**: Instead of one DB, we strictly enforce **Polyglot Persistence**.
    - **RDF/SPARQL**: Added to test "Semantic/Ontological" queries.
    - **HBase**: Added to test "Wide-Column/Big Data" patterns.
    - **Reasoning**: This allows us to publish results like "Graph DBs perform 20% better on 'traversal' questions than Document DBs."

#### 3. From Direct Generation to "SMART" Pipeline
- **Perception**: LLMs hallucinate syntax for rare DBs (like Cypher or SPARQL).
- **Change**: Adopted the **SMART-lite** loop.
    - **IR Layer**: First generate abstract intent (Find, Filter) -> Then compile to DB syntax.
    - **Execution Loop**: If the generated SPARQL query fails, feed the error back to Gemini to fix it.

#### 4. From "Trust" to "Safe-by-Default"
- **Perception**: Enterprise/Research constraints (Yang, 2025) demand safety.
- **Change**: Added `src/validation/policy.py`. Writes are blocked by default.

## Future Vision (Version 3?)
- **Multi-Agent**: One agent for "Schema Discovery", one for "Query Gen", one for "Review".
- **Fine-Tuning**: Moving from RAG to fine-tuned SLMs for specific DB dialects.
