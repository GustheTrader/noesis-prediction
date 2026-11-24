"""
CLI:  python -m data_agent [options]

  python -m data_agent --domain MLB \
      --schema ../GNOESIS_ontology/schema/gnoesis.json \
      --data mlb_first5/data/processed/test_data.csv \
      --data mlb_first5/data/processed/train_data.csv \
      --out reports/ontology

Live Neo4j is read automatically when NEO4J_URI and NEO4J_PASSWORD are set
(NEO4J_USER, NEO4J_DATABASE optional). Nothing is written to Neo4j unless
--load is passed.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from .agent import DEFAULT_TARGETS, DataAgent
from .graph_source import save_snapshot

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA = ROOT / "mlb_first5" / "data" / "processed" / "test_data.csv"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="data_agent", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", action="append", help="CSV/JSON/JSONL test data (repeatable)")
    ap.add_argument("--target", action="append", help="outcome column(s)")
    ap.add_argument("--schema", help="graph schema snapshot JSON (GNOESIS format)")
    ap.add_argument("--cypher", action="append", default=[], help=".cypher file or dir (repeatable)")
    ap.add_argument("--domain", help="domain prefix for clashing labels, e.g. MLB")
    ap.add_argument("--model", default="noesis", help="model name stamped on Prediction nodes")
    ap.add_argument("--max-rows", type=int)
    ap.add_argument("--out", default=str(ROOT / "reports" / "ontology"))
    ap.add_argument("--save-graph", help="write the merged graph snapshot here")
    ap.add_argument("--load", action="store_true",
                    help="WRITE: apply DDL and MERGE rows into Neo4j (needs NEO4J_* env)")
    ap.add_argument("-v", "--verbose", action="store_true")
    a = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    logging.basicConfig(level=logging.INFO if a.verbose else logging.WARNING,
                        format="%(levelname)s %(name)s: %(message)s")

    agent = DataAgent(domain=a.domain, model_name=a.model)
    agent.ingest_graph(snapshot=a.schema, cypher_roots=a.cypher)
    if a.save_graph:
        save_snapshot(agent.graph, a.save_graph)
    agent.ingest_data(a.data or [DEFAULT_DATA], targets=a.target or DEFAULT_TARGETS,
                      max_rows=a.max_rows)
    agent.propose()
    files = agent.write(a.out)
    print(agent.summary())
    for f in agent.proposal.findings:
        print(f"  [{f.severity}] {f.message}")
    for kind, path in files.items():
        print(f"  {kind:6} {path}")
    if a.load:
        n = agent.load()
        print(f"loaded {n:,} unique rows into Neo4j")
    return 0


if __name__ == "__main__":
    sys.exit(main())
