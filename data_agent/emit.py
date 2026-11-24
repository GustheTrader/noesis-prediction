"""
Emit — the reviewable artifacts.

  proposal.md            read first: findings, types, where each column lands
  proposal.json          machine-readable; diff it against the next run
  proposal.cypher        DDL only: IF NOT EXISTS constraints/indexes, no DROP/DELETE/SET
  load_template.cypher   parameterized UNWIND $rows MERGE … to load the data
                         into the proposed shape (run only after the DDL)

Nothing here touches a database.
"""

from __future__ import annotations

import json
from pathlib import Path

from .ontology import EntityProposal, OntologyProposal

_DDL_STATUSES = ("NEW", "RENAMED")


def _q(name: str) -> str:
    return "`" + name.replace("`", "``") + "`"


def _val(column: str, dtype: str) -> str:
    ref = f"row.{_q(column)}"
    if dtype == "date":
        return f"date({ref})"
    return ref


def ddl(p: OntologyProposal) -> str:
    lines = [
        "// NOESIS data agent — ontology proposal (DDL only)",
        f"// graph: {p.graph_origin}   data: {', '.join(p.sources)}",
        "// Idempotent (IF NOT EXISTS) and non-destructive: no DROP, DELETE or SET.",
        "",
    ]
    for e in p.entities:
        if e.status not in _DDL_STATUSES:
            continue
        lines.append(f"// {e.status} {e.label}  ({e.distinct:,} distinct, key from {e.key_column})")
        lines.append(f"CREATE CONSTRAINT {e.label.lower()}_{e.key_prop}_unique IF NOT EXISTS "
                     f"FOR (n:{_q(e.label)}) REQUIRE n.{_q(e.key_prop)} IS UNIQUE;")
        for pm in e.props:
            if pm.dtype == "date":
                lines.append(f"CREATE INDEX {e.label.lower()}_{pm.prop}_idx IF NOT EXISTS "
                             f"FOR (n:{_q(e.label)}) ON (n.{_q(pm.prop)});")
        lines.append("")
    unresolved = [e for e in p.entities if e.status == "UNRESOLVED"]
    for e in unresolved:
        lines.append(f"// UNRESOLVED {e.concept}: {e.reason} — no DDL emitted")
    rels = [r for r in p.relations if r.status == "NEW"]
    if rels:
        lines.append("// New relationship types (created by the load, no DDL needed):")
        for r in rels:
            lines.append(f"//   ({r.src})-[:{r.type}]->({r.dst})")
    return "\n".join(lines).rstrip() + "\n"


def _merge_node(var: str, e: EntityProposal) -> list[str]:
    out = [f"MERGE ({var}:{_q(e.label)} {{{_q(e.key_prop)}: {_val(e.key_column, e.key_dtype)}}})"]
    sets = [f"{var}.{_q(pm.prop)} = {_val(pm.column, pm.dtype)}"
            for pm in e.props if pm.column != "<model>"]
    if sets:
        out.append("SET " + ", ".join(sets))
    return out


def load_template(p: OntologyProposal) -> str:
    """One UNWIND statement that loads every row into the proposed shape."""
    usable = {e.concept: e for e in p.entities
              if e.status != "UNRESOLVED" and e.concept != "Prediction"}
    var = {}
    lines = [
        "// NOESIS data agent — load template. Parameters: $rows (list of row maps), $model.",
        "// Run proposal.cypher first. Review before running: this one DOES write.",
        "UNWIND $rows AS row",
    ]
    for i, (concept, e) in enumerate(usable.items()):
        v = f"n{i}"
        var[e.label] = v
        lines.extend(_merge_node(v, e))
    for j, r in enumerate(p.relations):
        if r.src not in var or r.dst not in var:
            continue
        rv = f"r{j}"
        lines.append(f"MERGE ({var[r.src]})-[{rv}:{_q(r.type)}]->({var[r.dst]})")
        sets = [f"{rv}.{_q(pm.prop)} = {_val(pm.column, pm.dtype)}" for pm in r.props]
        if sets:
            lines.append("SET " + ", ".join(sets))

    pred = next((e for e in p.entities if e.concept == "Prediction"
                 and e.status != "UNRESOLVED"), None)
    event = next((e for e in p.entities if e.is_event), None)
    subject = next((e for e in p.entities if e.is_subject), None)
    if pred and event and subject and event.label in var and subject.label in var:
        key = (f"toString(row.{_q(event.key_column)}) + ':' + "
               f"toString(row.{_q(subject.key_column)}) + ':' + $model")
        lines.append(f"MERGE (pr:{_q(pred.label)} {{{_q(pred.key_prop)}: {key}}})")
        sets = [f"pr.{_q(pm.prop)} = {_val(pm.column, pm.dtype)}"
                for pm in pred.props if pm.column != "<model>"] + ["pr.model = $model"]
        lines.append("SET " + ", ".join(sets))
        lines.append(f"MERGE (pr)-[:PREDICTS]->({var[event.label]})")
        lines.append(f"MERGE (pr)-[:ABOUT]->({var[subject.label]})")
    return "\n".join(lines) + ";\n"


def markdown(p: OntologyProposal) -> str:
    L = ["# NOESIS data agent — ontology proposal", ""]
    L.append(f"- **Data:** {', '.join(p.sources)}")
    L.append(f"- **Rows:** {p.raw_rows:,} raw → {p.unique_rows:,} unique")
    L.append(f"- **Graph:** {p.graph_origin}")
    L.append("")
    if p.findings:
        L += ["## Findings", ""]
        order = {"high": 0, "medium": 1, "info": 2}
        for f in sorted(p.findings, key=lambda f: order.get(f.severity, 3)):
            L.append(f"- **{f.severity.upper()}** — {f.message}")
        L.append("")

    L += ["## Node types", "", "| Status | Label | Key | Distinct | Why |", "|---|---|---|---|---|"]
    for e in p.entities:
        tag = " (event)" if e.is_event else " (subject)" if e.is_subject else ""
        L.append(f"| {e.status} | `{e.label}`{tag} | `{e.key_prop}` ← `{e.key_column}` "
                 f"| {e.distinct:,} | {e.reason} |")
    L.append("")

    L += ["## Relationship types", "", "| Status | Pattern | Why |", "|---|---|---|"]
    for r in p.relations:
        L.append(f"| {r.status} | `({r.src})-[:{r.type}]->({r.dst})` | {r.reason} |")
    L.append("")

    L += ["## Where each column lands", "",
          "Grain comes from a functional-dependency test on the unique rows: "
          "`stable` = fixed per entity, `season` = fixed per entity+season, "
          "`event` = varies per game, `unproven` = too few repeat ids to tell (placed per game), "
          "`assumed` = a `*_name` label column with no evidence against it.",
          "", "| Column | Lands on | Property | Grain |", "|---|---|---|---|"]
    for e in p.entities:
        L.append(f"| `{e.key_column}` | `{e.label}` | `{e.key_prop}` (key) | identity |")
        for pm in e.props:
            L.append(f"| `{pm.column}` | `{e.label}` | `{pm.prop}` | {pm.evidence} |")
    for r in p.relations:
        for pm in r.props:
            L.append(f"| `{pm.column}` | `-[:{r.type}]->` ({r.src}→{r.dst}) | `{pm.prop}` | {pm.evidence} |")
    for col, why in p.excluded_columns.items():
        L.append(f"| `{col}` | — | — | excluded: {why} |")
    L += ["", "## Apply", "",
          "1. Review this file.",
          "2. `cypher-shell -u neo4j -p <pw> < proposal.cypher` (idempotent, adds types only).",
          "3. Load rows with `load_template.cypher` (`$rows`, `$model`) — or "
          "`python -m data_agent ... --load` once you are happy with the shape.", ""]
    return "\n".join(L)


def write_all(p: OntologyProposal, out_dir: str | Path) -> dict[str, Path]:
    d = Path(out_dir)
    d.mkdir(parents=True, exist_ok=True)
    files = {
        "md": d / "proposal.md",
        "json": d / "proposal.json",
        "cypher": d / "proposal.cypher",
        "load": d / "load_template.cypher",
    }
    files["md"].write_text(markdown(p), encoding="utf-8")
    files["json"].write_text(json.dumps(p.to_dict(), indent=2, default=str), encoding="utf-8")
    files["cypher"].write_text(ddl(p), encoding="utf-8")
    files["load"].write_text(load_template(p), encoding="utf-8")
    return files
