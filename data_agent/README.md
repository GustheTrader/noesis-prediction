# NOESIS Data Agent

Takes in **Neo4j graph data** plus **test data** and proposes a better ontology:
which node and relationship types the data needs, where each column should live,
and how it fits the graph that already exists, with evidence for every call.

```
Neo4j (live)  ─┐
schema JSON   ─┼─► graph snapshot ─┐
.cypher files ─┘                   ├─► infer + align ─► proposal.{md,json,cypher} + load_template.cypher
test data (CSV/JSON/JSONL) ─► profile (dedupe, roles, grain) ─┘
```

Reading never writes anything. `--load` is the only write path.

## Run

```bash
# against the GNOESIS schema snapshot (no database needed)
python -m data_agent --domain MLB \
  --schema ../GNOESIS_ontology/schema/gnoesis.json \
  --data mlb_first5/data/processed/test_data.csv \
  --data mlb_first5/data/processed/train_data.csv

# against the live graph (pip install neo4j)
export NEO4J_URI=bolt://localhost:7687 NEO4J_USER=neo4j NEO4J_PASSWORD=...
python -m data_agent --domain MLB --data mlb_first5/data/processed/test_data.csv

# after reviewing reports/ontology/proposal.md: apply DDL + MERGE the rows
python -m data_agent --domain MLB --data ... --load
```

Output goes to `reports/ontology/` by default (`--out` changes it).

```python
from data_agent import DataAgent
agent = DataAgent(domain="MLB")
agent.ingest_graph(snapshot="../GNOESIS_ontology/schema/gnoesis.json")
agent.ingest_data(["mlb_first5/data/processed/test_data.csv"], targets=["first_5_runs_allowed"])
print(agent.summary()); agent.write("reports/ontology")
```

## How it decides

**Entities come from identifiers.** `pitcher_id` → `Pitcher`, `event_id` → `Game`.
Columns sharing the prefix belong to that entity (`pitcher_era` → Pitcher).
The event is the identifier that fixes the date and covers only a few rows each.

**Grain comes from a functional-dependency test**, run on the unique rows:

| Data shows | Lands on |
|---|---|
| fixed per entity | node property (`Pitcher.name`) |
| fixed per entity + season | `(Pitcher)-[:IN_SEASON {era}]->(Season)` |
| varies within a season | `(Pitcher)-[:IN_GAME {era}]->(MLB_Game)` |
| too few repeat ids to tell | per game, marked `unproven` (never wrong) |

**Alignment with the graph:**

| Status | Meaning |
|---|---|
| `REUSE` | label exists and its key is compatible (`Season.year`) |
| `RENAMED` | concept exists, but its key is another identity space. NFL `Team.code` vs MLB `team_id` becomes `MLB_Team`, following the graph's own `CFB_Team` precedent |
| `NEW` | not in the graph |
| `UNRESOLVED` | clash with no `--domain` given: reported, no DDL emitted |

With a live graph it also samples key **values**, so a label whose key *name*
matches but whose values are of another type (`"KC"` vs `14`) is still caught.

Predictions (`predicted_*`, `edge_*`) become `Prediction` nodes, linked
`-[:PREDICTS]->` the game and `-[:ABOUT]->` the pitcher, so they can be scored
against outcomes inside the graph.

## Safety

- `proposal.cypher` is DDL only: every statement is `IF NOT EXISTS`; no `DROP`, `DELETE` or `SET`.
- Labels are emitted verbatim (`CFB_Game`, never `CFBGame`). Names are folded only for comparison.
- Exact-duplicate rows are dropped before inference and reported.
- Live reads use a `READ` session.

## Tests

```bash
python -m unittest discover -s data_agent/tests -t .
```

No pytest or Neo4j needed. `--load` was verified separately against a throwaway Neo4j 5
container: loading twice gives the same counts, NFL `Team` nodes are untouched, and a
re-read after loading reports every type as `REUSE`.
