# How to Run: NoSQL NLQ System

## Prerequisites
1.  **Python 3.10+**
2.  **Docker & Docker Compose** (for database containers)
3.  **Google Gemini API Key** (Set as `GEMINI_API_KEY`)

## Installation
1.  Clone the repository.
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Create `.env` file:
    ```ini
    GEMINI_API_KEY=your_key_here
    ```

## Setting up Databases
We provide a Docker Compose file to spin up MongoDB, Redis, Neo4j, and HBase.

```bash
docker-compose up -d
```

### Ingesting Sample Data
Once containers are up, load the data:
```bash
python lecture.py
```
*(Note: Requires `lecture.py` to be updated or compatible with the new structure. The legacy script imports into Mongo/Redis/Neo4j).*

## Using the CLI
The system operates via a unified CLI.

### Syntax
```bash
python src/cli.py --db <DB_TYPE> --query "<YOUR QUERY>" [--unsafe] [--details]
```

### Supported DB Types
- `mongo` (MongoDB)
- `redis` (Redis)
- `neo4j` (Neo4j)
- `rdf` (In-Memory RDF Graph - No Docker needed)
- `hbase` (HBase)

### Examples

**1. MongoDB (Filtering & Aggregation)**
```bash
python src/cli.py --db mongo --query "Find all movies directed by Nolan"
```

**2. Neo4j (Graph Traversal)**
```bash
python src/cli.py --db neo4j --query "Who acted in Inception?"
```

**3. RDF (Semantic / SPARQL)**
```bash
python src/cli.py --db rdf --query "What is the type of entity 'Inception'?"
```

**4. Safety Mode (Writes)**
By default, writes are blocked. To allow them:
```bash
python src/cli.py --db redis --query "SET movie:99:rating 5" --unsafe
```

## Troubleshooting
- **Connection Error**: Ensure Docker containers are running (`docker ps`).
- **LLM Error**: Check your `GEMINI_API_KEY`.
- **HBase Error**: Ensure port 9090 is verified exposed.
