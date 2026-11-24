"""
DataAgent — takes in Neo4j graph data plus test data, proposes a better ontology.

    agent = DataAgent(domain="MLB")
    agent.ingest_graph(snapshot="schema/gnoesis.json")   # and/or live NEO4J_* env
    agent.ingest_data(["mlb_first5/data/processed/test_data.csv"],
                      targets=["first_5_runs_allowed"])
    proposal = agent.propose()
    agent.write("reports/ontology")

Reading is the default and is always safe. ``load()`` is the only method that
writes to Neo4j, and it runs only when called explicitly (``--load`` on the CLI).
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable, Optional, Sequence

from . import emit
from .graph_source import (GraphSnapshot, Neo4jConfig, from_cypher_files, from_neo4j,
                           load_snapshot, merge)
from .ontology import OntologyProposal, infer
from .profiler import DatasetProfile, dedupe, profile, read_records

log = logging.getLogger("data_agent")

DEFAULT_TARGETS = ("first_5_runs_allowed",)


class DataAgent:
    name = "data_agent"

    def __init__(self, domain: Optional[str] = None, model_name: str = "noesis"):
        self.domain = domain
        self.model_name = model_name
        self.graph = GraphSnapshot()
        self.profile: Optional[DatasetProfile] = None
        self.proposal: Optional[OntologyProposal] = None

    # ── intake ──

    def ingest_graph(self, snapshot: Optional[str | Path] = None,
                     cypher_roots: Iterable[str | Path] = (),
                     neo4j: Optional[Neo4jConfig] = None) -> GraphSnapshot:
        """Union every graph source given. Live Neo4j is used when configured."""
        parts: list[GraphSnapshot] = []
        errors: list[str] = []
        cfg = neo4j or Neo4jConfig.from_env()
        if cfg.configured:
            live = from_neo4j(cfg)
            if live.error:
                errors.append(live.error)
            parts.append(live)
        if snapshot:
            parts.append(load_snapshot(snapshot))
        roots = list(cypher_roots)
        if roots:
            parts.append(from_cypher_files(roots))
        self.graph = merge(*parts) if parts else GraphSnapshot()
        if errors:
            self.graph.error = "; ".join(errors)
        elif not parts:
            self.graph.error = "no graph source (set NEO4J_URI/NEO4J_PASSWORD or pass --schema)"
        log.info("graph: %d labels, %d relation types (%s)", len(self.graph.labels),
                 len(self.graph.relations), self.graph.origin or "none")
        return self.graph

    def ingest_data(self, paths: Sequence[str | Path], targets: Sequence[str] = DEFAULT_TARGETS,
                    max_rows: Optional[int] = None) -> DatasetProfile:
        """Profile one or more files as a single dataset (union of rows)."""
        rows: list[dict] = []
        for path in paths:
            rows.extend(read_records(path, max_rows=max_rows))
        self.profile = profile(";".join(str(p) for p in paths), targets=targets, rows=rows)
        log.info("data: %d rows -> %d unique, %d columns", self.profile.raw_rows,
                 self.profile.unique_rows, len(self.profile.columns))
        return self.profile

    # ── reasoning ──

    def propose(self) -> OntologyProposal:
        if self.profile is None:
            raise RuntimeError("ingest_data() first")
        self.proposal = infer(self.profile, self.graph, domain=self.domain,
                              model_name=self.model_name)
        return self.proposal

    def write(self, out_dir: str | Path) -> dict[str, Path]:
        if self.proposal is None:
            self.propose()
        return emit.write_all(self.proposal, out_dir)

    def summary(self) -> str:
        p = self.proposal or self.propose()
        counts: dict[str, int] = {}
        for e in p.entities:
            counts[e.status] = counts.get(e.status, 0) + 1
        new_rels = sum(1 for r in p.relations if r.status == "NEW")
        return (f"{p.unique_rows:,} unique rows (of {p.raw_rows:,}); node types "
                + ", ".join(f"{k} {v}" for k, v in sorted(counts.items()))
                + f"; {new_rels} new / {len(p.relations) - new_rels} reused relation types; "
                  f"{len(p.findings)} findings")

    # ── the only write path ──

    def load(self, neo4j: Optional[Neo4jConfig] = None, batch: int = 500) -> int:
        """Apply proposal DDL and MERGE the unique rows. Explicit call only."""
        if self.proposal is None or self.profile is None:
            raise RuntimeError("propose() first")
        cfg = neo4j or Neo4jConfig.from_env()
        if not cfg.configured:
            raise RuntimeError("NEO4J_URI / NEO4J_PASSWORD not set")
        from neo4j import GraphDatabase  # optional dependency

        statements = [s.strip() for s in emit.ddl(self.proposal).split(";")
                      if s.strip() and not all(l.startswith("//") for l in s.strip().splitlines())]
        template = emit.load_template(self.proposal)
        rows = [{k: (v.isoformat() if hasattr(v, "isoformat") else v) for k, v in r.items()}
                for r in dedupe(self.profile.rows)]
        drv = GraphDatabase.driver(cfg.uri, auth=(cfg.user, cfg.password))
        try:
            with drv.session(database=cfg.database) as s:
                for stmt in statements:
                    s.run(stmt).consume()
                for i in range(0, len(rows), batch):
                    s.run(template, rows=rows[i:i + batch], model=self.model_name).consume()
        finally:
            drv.close()
        return len(rows)
