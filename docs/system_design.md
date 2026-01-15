# System Design: LLM-Assisted NoSQL Query Engine

## 1. Architectural Strategy: Polyglot Persistence

To answer the core design question: **"Same database or suitable format for each?"**

We adopt a **Polyglot Persistence** strategy.
- **Concept**: We use a single *logical* dataset (e.g., "Movies"), but we replicate and project this data into the **native format** of each NoSQL system.
- **Rationale**: This allows us to benchmark the "Text-to-NoSQL" capabilities fairly. We want to see how the LLM handles *Graph* traversal (Neo4j) vs *Document* filtering (Mongo) for the same underlying information.

### Data Mapping Strategy
| Logical Entity | MongoDB (Document) | Neo4j (Graph) | Redis (Key-Value) |
| :--- | :--- | :--- | :--- |
| **Movie** | `movies` Collection (JSON Doc) | `:Movie` Node | `movie:{id}:info` (Hash) |
| **Director** | Field `director` (String) | `:Director` Node + `[:DIRECTED]` Rel | N/A (or secondary index) |
| **Actor** | Field `actors` (Array) | `:Actor` Node + `[:ACTED_IN]` Rel | N/A |
| **Stats** | Field `rating` | Property `rating` | `movie:{id}:views` (Counter) |
| **Semantic** | N/A | N/A | N/A |
| **Metadata** | `details` Object | Properties | `movie:{id}:meta` (Hash) |

### Additional Paradigms (Research Extensions)
| Logical Entity | RDF / SPARQL (Semantic) | HBase (Wide Column) |
| :--- | :--- | :--- |
| **Movie** | `<http://ex.org/movie/{id}>` `rdf:type` `:Movie` | RowKey: `mov_{id}` |
| **Director** | Triple: `... :directedBy <dir_uri>` | Col: `credits:director` |
| **Relation** | Ontology-based properties | ColFamily grouping |

## 2. High-Level Architecture

```ascii
       [User / CLI]
            │ (NLQ: "Who directed Inception?")
            ▼
    +-------------------+
    |   Orchestrator    |  <-- "Smart-Lite" Pipeline
    +---------+---------+
              │
    +---------▼---------+       (1) Metadata Discovery
    | Schema Inference  | <---- (Connectors query DBs)
    +---------+---------+
              │
    +---------▼---------+       (2) IR Generation
    |   LLM (Gemini)    | ----> (JSON Intermediate Rep)
    +---------+---------+
              │
    +---------▼---------+       (3) Validation Gate
    |  Policy Check     | <---- (Reject Writes/Unsafe)
    +---------+---------+
              │
    +---------▼---------+       (4) Execution
    |   Connectors      | ----> [MongoDB] / [Neo4j] / [Redis]
    +---------+---------+
              │
    +---------▼---------+       (5) Refinement Loop
    | Execution Feedback| ----> (If Error: Retry with History)
    +-------------------+
```

## 3. Module Responsibilities

### Module A: Connectors (`src/connectors/`)
- Unified Interface: `get_metadata()`, `execute()`.
- **Mongo**: Infers schema from recent documents.
- **Neo4j**: Fetches labels and relationship types.
- **Redis**: Scans keys to infer patterns (e.g., `user:*:profile`).
- **RDF/SPARQL**: Uses `rdflib` (in-memory or Fuseki) to query triples.
- **HBase**: Uses `happybase` (Thrift) to scan column families.

### Module B: Intermediate Representation (IR)
Decouples "Intent" from "Syntax".
- **Intent**: `FIND`, `AGGREGATE`, `TRAVERSE`.
- **Entities**: Which collections/nodes?
- **Filters**: Abstract filters (`year > 2010`).

### Module C: Validation & Safety
- **Read-Only Default**: All queries parsed for mutation keywords (`INSERT`, `DELETE`, `MERGE`, `SET`).
- **Explicit Override**: CLI requires `--unsafe` flag or "Yes" confirmation for mutations.

## 4. Requirement Traceability
| Literature Claim | Implementation |
| :--- | :--- |
| "Schema heterogeneity requires structural IR" (Qin et al.) | `src/ir/models.py` (Pydantic models) |
| "Execution feedback improves accuracy" (Lu et al.) | `src/pipeline/smart.py` (Retry loop) |
| "Safety validation is mandatory" (Yang) | `src/validation/policy.py` |

