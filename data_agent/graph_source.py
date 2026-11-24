"""
Graph source — what the Neo4j graph already contains.

The data agent proposes ADDITIONS to the real graph, so it has to know the real
graph first. Three ways to get it, best first:

  1. Live Neo4j (``from_neo4j``) — labels, relationship types, unique keys,
     sampled property names, node counts, observed (src)-[r]->(dst) patterns
     and sample key VALUES. Needs the optional ``neo4j`` driver.
  2. A schema snapshot JSON (``load_snapshot``) — the format written by
     GNOESIS_ontology's ``evolve_schema.py --save-schema`` and by this module's
     ``save_snapshot``.
  3. ``.cypher`` files (``from_cypher_files``) — constraints and MERGE labels.

The source never invents a schema. If Neo4j is unreachable it returns an EMPTY
snapshot with ``error`` set, so the caller can tell "no graph" apart from
"graph with no labels".
"""

from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable, Optional

log = logging.getLogger("data_agent.graph")


def fold(name: str) -> str:
    """Comparison key only — never emitted as a label.

    Neo4j treats ``CFB_Game`` and ``CFBGame`` as different labels, so names are
    always emitted verbatim; ``fold`` only decides whether two names mean the
    same thing.
    """
    return re.sub(r"[^a-z0-9]+", "", (name or "").lower())


@dataclass
class GraphLabel:
    name: str
    unique_keys: list[str] = field(default_factory=list)
    props: list[str] = field(default_factory=list)
    count: Optional[int] = None
    # A few key values per unique key, from the live graph. Used to detect a
    # label that has the right NAME but a different identity domain (NFL team
    # codes "KC" vs MLB numeric team ids).
    key_samples: dict[str, list] = field(default_factory=dict)

    @property
    def key(self) -> Optional[str]:
        return self.unique_keys[0] if self.unique_keys else None


@dataclass
class GraphRelation:
    name: str
    patterns: list[tuple[str, str]] = field(default_factory=list)
    count: Optional[int] = None


@dataclass
class GraphSnapshot:
    labels: dict[str, GraphLabel] = field(default_factory=dict)
    relations: dict[str, GraphRelation] = field(default_factory=dict)
    origin: str = ""
    error: Optional[str] = None

    # ── lookup by meaning, return verbatim name ──

    def find_label(self, name: str) -> Optional[GraphLabel]:
        f = fold(name)
        for k, v in self.labels.items():
            if fold(k) == f:
                return v
        return None

    def find_relation(self, name: str) -> Optional[GraphRelation]:
        f = fold(name)
        for k, v in self.relations.items():
            if fold(k) == f:
                return v
        return None

    def domain_prefixes(self) -> list[str]:
        """Sport/domain prefixes the graph already uses, e.g. ``CFB`` from
        ``CFB_Game``. A second domain living beside a base label is the graph's
        own convention for keeping identity spaces apart."""
        out = []
        for k in self.labels:
            m = re.match(r"^([A-Z]{2,5})_[A-Z]", k)
            if m and m.group(1) not in out:
                out.append(m.group(1))
        return out

    @property
    def empty(self) -> bool:
        return not self.labels

    def to_dict(self) -> dict:
        return {
            "origin": self.origin,
            "error": self.error,
            "nodes": {k: asdict(v) for k, v in sorted(self.labels.items())},
            "relations": {k: {"name": v.name, "patterns": [list(p) for p in v.patterns],
                              "count": v.count}
                          for k, v in sorted(self.relations.items())},
            "counts": {"nodes": len(self.labels), "relations": len(self.relations)},
        }


# ---------------------------------------------------------------------------
# Snapshot JSON (GNOESIS_ontology format is a subset of ours)
# ---------------------------------------------------------------------------

def load_snapshot(path: str | Path) -> GraphSnapshot:
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    snap = GraphSnapshot(origin=d.get("origin") or f"snapshot:{Path(path).name}")
    for k, v in (d.get("nodes") or {}).items():
        snap.labels[k] = GraphLabel(
            name=v.get("name", k),
            unique_keys=list(v.get("unique_keys", [])),
            props=list(v.get("props", [])),
            count=v.get("count"),
            key_samples=dict(v.get("key_samples", {})),
        )
    for k, v in (d.get("relations") or {}).items():
        snap.relations[k] = GraphRelation(
            name=v.get("name", k),
            patterns=[tuple(p) for p in v.get("patterns", [])],
            count=v.get("count"),
        )
    return snap


def save_snapshot(snap: GraphSnapshot, path: str | Path) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(snap.to_dict(), indent=2, default=str), encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# .cypher files
# ---------------------------------------------------------------------------

_RE_CONSTRAINT = re.compile(
    r"CREATE\s+CONSTRAINT\s+\S+\s+IF\s+NOT\s+EXISTS\s+FOR\s+\(\s*\w*\s*:(\w+)\s*\)\s+"
    r"REQUIRE\s+([\w\.]+)\s+IS\s+UNIQUE", re.I | re.S)
_RE_LABEL = re.compile(r"(?:MERGE|CREATE|MATCH)\s*\(\s*\w*\s*:(\w+)", re.I)
_RE_REL = re.compile(r"\[\s*\w*\s*:\s*(\w+)\s*[\]\{ ]")


def from_cypher_files(roots: Iterable[str | Path]) -> GraphSnapshot:
    snap = GraphSnapshot(origin="cypher")
    for root in roots:
        p = Path(root)
        files = [p] if p.is_file() else sorted(p.rglob("*.cypher")) if p.is_dir() else []
        for f in files:
            text = f.read_text(encoding="utf-8", errors="replace")
            for label, prop in _RE_CONSTRAINT.findall(text):
                lbl = snap.labels.setdefault(label, GraphLabel(label))
                prop = prop.split(".", 1)[-1]
                if prop not in lbl.unique_keys:
                    lbl.unique_keys.append(prop)
            for label in _RE_LABEL.findall(text):
                snap.labels.setdefault(label, GraphLabel(label))
            for rel in _RE_REL.findall(text):
                snap.relations.setdefault(rel, GraphRelation(rel))
    return snap


# ---------------------------------------------------------------------------
# Live Neo4j
# ---------------------------------------------------------------------------

@dataclass
class Neo4jConfig:
    uri: Optional[str] = None
    user: str = "neo4j"
    password: Optional[str] = None
    database: str = "neo4j"

    @classmethod
    def from_env(cls) -> "Neo4jConfig":
        return cls(
            uri=os.environ.get("NEO4J_URI"),
            user=os.environ.get("NEO4J_USER", "neo4j"),
            password=os.environ.get("NEO4J_PASSWORD"),
            database=os.environ.get("NEO4J_DATABASE", "neo4j"),
        )

    @property
    def configured(self) -> bool:
        return bool(self.uri and self.password)


def _q(name: str) -> str:
    """Backtick-quote an identifier read from the database."""
    return "`" + name.replace("`", "``") + "`"


def from_neo4j(cfg: Neo4jConfig, sample: int = 200, pattern_limit: int = 20) -> GraphSnapshot:
    """Read the live graph (read-only queries only)."""
    snap = GraphSnapshot(origin=f"neo4j:{cfg.uri}")
    if not cfg.configured:
        snap.error = "NEO4J_URI / NEO4J_PASSWORD not set"
        return snap
    try:
        from neo4j import GraphDatabase
    except ImportError:
        snap.error = "neo4j driver not installed (pip install neo4j)"
        return snap

    try:
        drv = GraphDatabase.driver(cfg.uri, auth=(cfg.user, cfg.password))
        with drv.session(database=cfg.database, default_access_mode="READ") as s:
            for rec in s.run("CALL db.labels() YIELD label RETURN label"):
                snap.labels[rec["label"]] = GraphLabel(rec["label"])
            for rec in s.run("CALL db.relationshipTypes() YIELD relationshipType AS t RETURN t"):
                snap.relations[rec["t"]] = GraphRelation(rec["t"])

            # Unique keys (Neo4j 5 SHOW CONSTRAINTS).
            try:
                for rec in s.run("SHOW CONSTRAINTS YIELD type, labelsOrTypes, properties "
                                 "RETURN type, labelsOrTypes, properties"):
                    if "UNIQUE" not in (rec["type"] or "") and "KEY" not in (rec["type"] or ""):
                        continue
                    for lbl in rec["labelsOrTypes"] or []:
                        gl = snap.labels.setdefault(lbl, GraphLabel(lbl))
                        for p in rec["properties"] or []:
                            if p not in gl.unique_keys:
                                gl.unique_keys.append(p)
            except Exception as e:  # older servers
                log.warning("SHOW CONSTRAINTS failed: %s", e)

            for name, gl in snap.labels.items():
                gl.count = s.run(f"MATCH (n:{_q(name)}) RETURN count(n) AS c").single()["c"]
                rec = s.run(
                    f"MATCH (n:{_q(name)}) WITH n LIMIT $k UNWIND keys(n) AS key "
                    f"RETURN collect(DISTINCT key) AS keys", k=sample).single()
                gl.props = sorted(rec["keys"] or [])
                for key in gl.unique_keys:
                    vals = s.run(f"MATCH (n:{_q(name)}) WHERE n.{_q(key)} IS NOT NULL "
                                 f"RETURN n.{_q(key)} AS v LIMIT 10")
                    gl.key_samples[key] = [r["v"] for r in vals]

            for name, gr in snap.relations.items():
                rows = s.run(
                    f"MATCH (a)-[r:{_q(name)}]->(b) WITH labels(a)[0] AS src, labels(b)[0] AS dst "
                    f"RETURN src, dst, count(*) AS c ORDER BY c DESC LIMIT $k", k=pattern_limit)
                total = 0
                for r in rows:
                    gr.patterns.append((r["src"], r["dst"]))
                    total += r["c"]
                gr.count = total
        drv.close()
    except Exception as e:
        log.warning("live Neo4j read failed: %s", e)
        return GraphSnapshot(origin=snap.origin, error=f"Neo4j read failed: {e}")
    return snap


def merge(*snaps: GraphSnapshot) -> GraphSnapshot:
    """Union — a label seen in any source exists. Live data wins on counts/samples."""
    out = GraphSnapshot(origin="+".join(s.origin for s in snaps if s.origin and not s.empty))
    for s in snaps:
        for k, v in s.labels.items():
            existing = out.find_label(k)
            if existing is None:
                out.labels[k] = GraphLabel(v.name, list(v.unique_keys), list(v.props),
                                           v.count, dict(v.key_samples))
                continue
            for attr in ("unique_keys", "props"):
                tgt = getattr(existing, attr)
                tgt.extend(x for x in getattr(v, attr) if x not in tgt)
            existing.count = v.count if v.count is not None else existing.count
            existing.key_samples.update(v.key_samples)
        for k, v in s.relations.items():
            existing = out.find_relation(k)
            if existing is None:
                out.relations[k] = GraphRelation(v.name, list(v.patterns), v.count)
            else:
                existing.patterns.extend(p for p in v.patterns if p not in existing.patterns)
                existing.count = v.count if v.count is not None else existing.count
    return out
