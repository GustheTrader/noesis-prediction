"""
Ontology inference + alignment — test data shape, reconciled with the graph.

Two questions per column, both answered from the data:

1. **Which entity does it describe?** Identifier columns become entities
   (``pitcher_id`` -> Pitcher, ``event_id`` -> Game). Columns sharing an
   identifier's prefix belong to it (``pitcher_era`` -> Pitcher).

2. **At what grain does it vary?** A functional-dependency test decides where
   a property lives:

     stable per entity           -> node property      (Pitcher.name)
     stable per entity + season  -> season-scoped      (Pitcher -[:PITCHER_OF {season}]-> Team)
     varies per event            -> relationship prop  (Pitcher -[:IN_GAME {era}]-> Game)

   Stability is only claimed with evidence: ids seen once prove nothing, so a
   column with too few repeat ids is placed at the finest grain (per event,
   never wrong) and reported as UNPROVEN.

Then every inferred type is aligned with the graph:

  REUSE    the label/relation exists and its key is compatible
  RENAMED  the concept exists but its key belongs to another identity space
           (NFL ``Team.code`` vs MLB ``team_id``) -> domain-prefixed label,
           following the graph's own ``CFB_Game`` convention
  NEW      not in the graph
  UNRESOLVED a conflict with no safe name -> reported, no DDL emitted
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from typing import Optional, Sequence

from .graph_source import GraphLabel, GraphSnapshot, fold
from .profiler import ColumnProfile, DatasetProfile, _split_camel_id

EVENT_SYNONYMS = {"event": "Game", "game": "Game", "match": "Game", "fixture": "Game"}
RESERVED_KEYS = {"id", "name", "uuid", "summary", "created_at"}
STABLE = 0.95          # share of repeat ids that must agree
MIN_REPEAT_IDS = 5     # repeat ids needed before stability is believed


# ---------------------------------------------------------------------------
# Naming
# ---------------------------------------------------------------------------

def pascal(raw: str) -> str:
    parts = re.split(r"[^A-Za-z0-9]+", raw or "")
    return "".join(p[:1].upper() + p[1:] for p in parts if p)


def camel(raw: str) -> str:
    p = pascal(raw)
    return p[:1].lower() + p[1:]


def screaming(raw: str) -> str:
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", raw or "")
    return re.sub(r"[^A-Za-z0-9]+", "_", s).strip("_").upper()


# ---------------------------------------------------------------------------
# Proposal model
# ---------------------------------------------------------------------------

@dataclass
class PropMap:
    prop: str            # graph property name
    column: str          # source column
    dtype: str
    evidence: str        # stable | season | event | unproven


@dataclass
class EntityProposal:
    concept: str
    label: str
    status: str                      # REUSE | NEW | RENAMED | UNRESOLVED
    key_column: str
    key_prop: str
    key_dtype: str
    distinct: int
    props: list[PropMap] = field(default_factory=list)
    is_event: bool = False
    is_subject: bool = False
    matched_label: Optional[str] = None
    reason: str = ""


@dataclass
class RelationProposal:
    type: str
    src: str
    dst: str
    status: str                      # REUSE | NEW
    props: list[PropMap] = field(default_factory=list)
    support: int = 0
    reason: str = ""


@dataclass
class Finding:
    severity: str                    # high | medium | info
    message: str


@dataclass
class OntologyProposal:
    sources: list[str]
    raw_rows: int
    unique_rows: int
    graph_origin: str
    entities: list[EntityProposal] = field(default_factory=list)
    relations: list[RelationProposal] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)
    excluded_columns: dict[str, str] = field(default_factory=dict)

    def entity(self, concept: str) -> Optional[EntityProposal]:
        return next((e for e in self.entities if e.concept == concept), None)

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Dependency tests
# ---------------------------------------------------------------------------

def stability(rows: Sequence[dict], key: Sequence[str], col: str) -> tuple[Optional[float], int]:
    """Share of repeat keys whose `col` takes one value. (None, n) if too few."""
    groups: dict[tuple, set] = defaultdict(set)
    counts: dict[tuple, int] = defaultdict(int)
    for r in rows:
        k = tuple(r.get(x) for x in key)
        # A missing value is absence of evidence, not a second value.
        if any(v is None for v in k) or r.get(col) is None:
            continue
        counts[k] += 1
        groups[k].add(r.get(col))
    repeat = [k for k, c in counts.items() if c > 1]
    if len(repeat) < MIN_REPEAT_IDS:
        return None, len(repeat)
    return sum(1 for k in repeat if len(groups[k]) == 1) / len(repeat), len(repeat)


def _season_column(p: DatasetProfile) -> Optional[str]:
    for c in p.columns.values():
        if c.role == "temporal" and c.name.lower() in ("year", "season") and c.dtype == "int":
            return c.name
    return None


def _date_column(p: DatasetProfile) -> Optional[str]:
    for c in p.columns.values():
        if c.role == "temporal" and c.dtype == "date":
            return c.name
    return None


# ---------------------------------------------------------------------------
# Alignment
# ---------------------------------------------------------------------------

def _dtype_of(v) -> str:
    if isinstance(v, bool):
        return "bool"
    if isinstance(v, int):
        return "int"
    if isinstance(v, float):
        return "float"
    s = str(v)
    return "int" if re.fullmatch(r"[+-]?\d+", s) else "str"


def key_compatible(gl: GraphLabel, key_col: str, key_prop: str, key_dtype: str,
                   values: set) -> tuple[bool, str]:
    if not gl.unique_keys:
        return True, f"`{gl.name}` has no unique key; data key `{key_prop}` can be added"
    gk = gl.key
    if fold(gk) not in (fold(key_prop), fold(key_col)):
        return False, (f"`{gl.name}` is keyed by `{gk}`, the data by `{key_col}` — "
                       f"different identity spaces")
    samples = gl.key_samples.get(gk) or []
    if samples:
        gtypes = {_dtype_of(s) for s in samples}
        if key_dtype not in gtypes and not ({key_dtype} | gtypes) <= {"int", "float"}:
            return False, (f"`{gl.name}.{gk}` holds {sorted(gtypes)} values "
                           f"(e.g. {samples[:3]}), the data holds {key_dtype}")
        overlap = {str(s) for s in samples} & {str(v) for v in values}
        if not overlap:
            return True, (f"`{gl.name}.{gk}` matches by name/type; no sampled value "
                          f"overlaps yet (new members of an existing type)")
    return True, f"`{gl.name}.{gk}` matches the data key `{key_col}`"


def align_entity(graph: GraphSnapshot, concept: str, key_col: str, key_dtype: str,
                 values: set, domain: Optional[str]) -> tuple[str, str, Optional[str], str, str]:
    """-> (status, label, matched_label, key_prop, reason)"""
    key_prop = camel(key_col)
    if key_prop.lower() in RESERVED_KEYS:
        key_prop = f"{camel(concept)}Id"

    prefixed = f"{domain}_{concept}" if domain else None
    if prefixed:
        gl = graph.find_label(prefixed)
        if gl is not None:
            ok, why = key_compatible(gl, key_col, key_prop, key_dtype, values)
            if ok:
                return "REUSE", gl.name, gl.name, gl.key or key_prop, why
            return "UNRESOLVED", gl.name, gl.name, key_prop, why

    gl = graph.find_label(concept)
    if gl is not None:
        ok, why = key_compatible(gl, key_col, key_prop, key_dtype, values)
        if ok:
            return "REUSE", gl.name, gl.name, gl.key or key_prop, why
        if prefixed:
            others = [f"{p}_{concept}" for p in graph.domain_prefixes()
                      if graph.find_label(f"{p}_{concept}")]
            precedent = f" (precedent: {', '.join(others)})" if others else ""
            return "RENAMED", prefixed, gl.name, key_prop, f"{why}; scoped as `{prefixed}`{precedent}"
        return "UNRESOLVED", concept, gl.name, key_prop, f"{why}; pass --domain to scope it"
    return "NEW", concept, None, key_prop, "not in the graph"


# ---------------------------------------------------------------------------
# Inference
# ---------------------------------------------------------------------------

def _owned_prop_name(col: ColumnProfile, prefix: Optional[str]) -> str:
    name = col.name
    if prefix and name.lower().startswith(prefix + "_"):
        name = name[len(prefix) + 1:]
    if name.lower() == "name":
        return "name"
    return camel(name)


def infer(p: DatasetProfile, graph: GraphSnapshot, domain: Optional[str] = None,
          model_name: str = "model") -> OntologyProposal:
    rows = p.rows
    out = OntologyProposal(sources=p.source.split(";"), raw_rows=p.raw_rows,
                           unique_rows=p.unique_rows,
                           graph_origin=graph.origin or "none")

    # ── data quality first: a wrong grain poisons every later step ──
    if p.duplicate_rows:
        sev = "high" if p.duplication_factor >= 2 else "medium"
        out.findings.append(Finding(sev, (
            f"{p.duplicate_rows:,} of {p.raw_rows:,} rows are exact duplicates "
            f"(each unique row repeats ~{p.duplication_factor:.0f}x). Inference used the "
            f"{p.unique_rows:,} unique rows. Any metric computed on the raw file "
            f"overstates its sample size by that factor.")))
    if graph.error:
        out.findings.append(Finding("medium", f"Graph source: {graph.error}. "
                                    f"Alignment used {graph.origin or 'no graph'}."))
    if graph.empty:
        out.findings.append(Finding("medium", "No graph schema loaded — every type is "
                                    "reported NEW; nothing can be confirmed as REUSE."))

    for c in p.columns.values():
        if c.dtype == "empty":
            out.excluded_columns[c.name] = "always empty"
        elif c.role == "prose":
            out.excluded_columns[c.name] = "free text — keep as a property, not a type"

    season_col = _season_column(p)
    date_col = _date_column(p)

    # ── entities from identifiers ──
    idents = [c for c in p.by_role("identifier") if c.name not in out.excluded_columns]
    bare = [c for c in idents if _split_camel_id(c.name) == ""]
    for c in bare:
        out.excluded_columns[c.name] = "bare `id` — row identity, not an entity"
    idents = [c for c in idents if c not in bare]

    def concept_of(c: ColumnProfile) -> str:
        pre = _split_camel_id(c.name) or c.name
        return EVENT_SYNONYMS.get(pre, pascal(pre))

    # Event: an identifier that fixes the date and covers few rows each.
    event_col: Optional[ColumnProfile] = None
    if date_col:
        best = None
        for c in idents:
            stab, _ = stability(rows, [c.name], date_col)
            per = p.unique_rows / max(c.distinct, 1)
            if (stab is None or stab >= STABLE) and per <= 4:
                score = (concept_of(c) == "Game", c.distinct)
                if best is None or score > best[0]:
                    best = (score, c)
        event_col = best[1] if best else None
    if event_col is None:
        for c in idents:
            if concept_of(c) == "Game":
                event_col = c

    owned: dict[str, list[ColumnProfile]] = defaultdict(list)
    for c in p.columns.values():
        if c.owner_prefix and c.name not in out.excluded_columns:
            owned[c.owner_prefix].append(c)

    non_event = [c for c in idents if c is not event_col]
    subject_col = max(non_event, key=lambda c: (len(owned[_split_camel_id(c.name)]),
                                                 -idents.index(c))) if non_event else None

    ents: dict[str, EntityProposal] = {}
    for c in idents:
        concept = concept_of(c)
        values = {r.get(c.name) for r in rows if r.get(c.name) is not None}
        status, label, matched, key_prop, reason = align_entity(
            graph, concept, c.name, c.dtype, values, domain)
        e = EntityProposal(concept=concept, label=label, status=status, key_column=c.name,
                           key_prop=key_prop, key_dtype=c.dtype, distinct=c.distinct,
                           is_event=c is event_col, is_subject=c is subject_col,
                           matched_label=matched, reason=reason)
        ents[c.name] = e
        out.entities.append(e)
        if status in ("RENAMED", "UNRESOLVED"):
            out.findings.append(Finding("high" if status == "UNRESOLVED" else "medium",
                                        f"{concept}: {reason}"))

    event = ents.get(event_col.name) if event_col else None
    subject = ents.get(subject_col.name) if subject_col else None

    def rel(rtype: str, src: EntityProposal, dst_label: str, reason: str) -> RelationProposal:
        existing = graph.find_relation(rtype)
        r = RelationProposal(type=existing.name if existing else rtype, src=src.label,
                             dst=dst_label, status="REUSE" if existing else "NEW",
                             support=p.unique_rows, reason=reason)
        out.relations.append(r)
        return r

    # Season: the graph already models it — resolve before placing properties so
    # season-scoped values have somewhere to live.
    season: Optional[EntityProposal] = None
    if season_col:
        status, label, matched, key_prop, reason = align_entity(
            graph, "Season", season_col, "int",
            {r.get(season_col) for r in rows if r.get(season_col) is not None}, None)
        season = EntityProposal(concept="Season", label=label, status=status,
                                key_column=season_col, key_prop=key_prop, key_dtype="int",
                                distinct=p.columns[season_col].distinct,
                                matched_label=matched, reason=reason)
        out.entities.append(season)

    in_season: dict[str, RelationProposal] = {}
    in_game: dict[str, RelationProposal] = {}
    if event:
        for col, e in ents.items():
            if e is not event:
                in_game[col] = rel("IN_GAME", e, event.label,
                                   f"each row places a {e.concept} in a {event.concept}")

    unproven: list[str] = []

    def place(col: ColumnProfile, e: EntityProposal, key_col: str, prop: str) -> None:
        stab, _ = stability(rows, [key_col], col.name)
        if stab is not None and stab >= STABLE:
            e.props.append(PropMap(prop, col.name, col.dtype, "stable"))
            return
        # `pitcher_name` next to `pitcher_id` is the entity's label by
        # construction. With no evidence either way, trust the pairing; if the
        # data shows it changing, the data wins and it falls through.
        if stab is None and col.role == "label":
            e.props.append(PropMap(prop, col.name, col.dtype, "assumed"))
            return
        sstab = None
        if season is not None and season_col != col.name:
            sstab, _ = stability(rows, [key_col, season_col], col.name)
            if sstab is not None and sstab >= STABLE:
                if key_col not in in_season:
                    in_season[key_col] = rel("IN_SEASON", e, season.label,
                                             f"{e.concept} values that change by season")
                in_season[key_col].props.append(PropMap(prop, col.name, col.dtype, "season"))
                return
        # Proven per-game only if it varies inside a season too; varying across
        # seasons with no within-season repeats could still be a season stat.
        if stab is None or (season is not None and season_col != col.name and sstab is None):
            evidence = "unproven"
            unproven.append(col.name)
        else:
            evidence = "event"
        target = in_game.get(key_col)
        if target is not None:
            target.props.append(PropMap(prop, col.name, col.dtype, evidence))
        else:
            e.props.append(PropMap(prop, col.name, col.dtype, evidence))

    # Owned columns (pitcher_era -> Pitcher).
    for col_name, e in ents.items():
        pre = _split_camel_id(col_name)
        for c in owned.get(pre, []):
            if c.role in ("prediction", "target", "identifier"):
                continue
            place(c, e, col_name, _owned_prop_name(c, pre))

    # Unowned columns: event-level if fixed per event, else on the subject's IN_GAME.
    preds = [c for c in p.columns.values() if c.role == "prediction"
             and c.name not in out.excluded_columns]
    targets = [c for c in p.columns.values() if c.role == "target"]
    categoricals = []
    for c in p.columns.values():
        if (c.owner_prefix or c.role in ("identifier", "prediction", "target")
                or c.name in out.excluded_columns or c.name == season_col):
            continue
        if c.role == "categorical":
            categoricals.append(c)
            continue
        if event and event_col is not None:
            stab, _ = stability(rows, [event_col.name], c.name)
            if stab is None or stab >= STABLE:
                event.props.append(PropMap(camel(c.name), c.name, c.dtype,
                                           "stable" if stab is not None else "unproven"))
                continue
        if subject is not None and subject_col is not None:
            place(c, subject, subject_col.name, camel(c.name))

    for c in targets:
        if subject_col is not None and subject_col.name in in_game:
            in_game[subject_col.name].props.append(PropMap(camel(c.name), c.name, c.dtype, "event"))

    # Entity -> entity membership (Pitcher -[:PITCHER_OF]-> Team).
    for col_a, a in ents.items():
        if a.is_event or not a.is_subject:
            continue
        for col_b, b in ents.items():
            if b is a or b.is_event:
                continue
            stab, n = stability(rows, [col_a], col_b)
            if stab is not None and stab >= STABLE:
                rel(f"{screaming(a.concept)}_OF", a, b.label,
                    f"`{col_b}` is fixed per `{col_a}` ({n} repeat ids)")
            elif season_col:
                sstab, n = stability(rows, [col_a, season_col], col_b)
                if sstab is not None and sstab >= STABLE:
                    r = rel(f"{screaming(a.concept)}_OF", a, b.label,
                            f"`{col_b}` is fixed per `{col_a}` within a season ({n} repeat ids)")
                    r.props.append(PropMap("season", season_col, "int", "season"))
                elif sstab is None:
                    unproven.append(f"{col_b}~{col_a}")

    if season is not None and event:
        rel("IN_SEASON", event, season.label, f"`{season_col}` is the season of each game")

    # Predictions become first-class nodes so they can be scored against outcomes.
    if preds and event and subject:
        status, label, matched, _, reason = align_entity(
            graph, "Prediction", "prediction_id", "str", set(), None)
        pe = EntityProposal(concept="Prediction", label=label, status=status,
                            key_column=f"{event.key_column}+{subject.key_column}+model",
                            key_prop="predictionId", key_dtype="str",
                            distinct=p.unique_rows, matched_label=matched,
                            reason=reason + f"; one per ({event.concept}, {subject.concept}, model)")
        pe.props = [PropMap(camel(c.name), c.name, c.dtype, "event") for c in preds]
        pe.props.append(PropMap("model", "<model>", "str", "stable"))
        out.entities.append(pe)
        rel("PREDICTS", pe, event.label, "a prediction is about one game")
        rel("ABOUT", pe, subject.label, f"a prediction is about one {subject.concept}")

    for c in categoricals:
        concept = pascal(c.name)
        status, label, matched, _, reason = align_entity(graph, concept, c.name, "str",
                                                         set(), domain)
        ce = EntityProposal(concept=concept, label=label, status=status, key_column=c.name,
                            key_prop="code", key_dtype="str", distinct=c.distinct,
                            matched_label=matched,
                            reason=reason + f"; {c.distinct} repeated values e.g. {c.examples}")
        out.entities.append(ce)
        if subject:
            rel(f"HAS_{screaming(c.name)}", subject, ce.label, f"categorical `{c.name}`")

    if unproven:
        out.findings.append(Finding("info", (
            f"{len(unproven)} placement(s) lack repeat ids to prove a grain "
            f"({', '.join(unproven[:6])}{'…' if len(unproven) > 6 else ''}). They sit at the "
            f"finest grain (per game), which is safe; more rows per entity per season "
            f"would let stable ones move up to node or season properties.")))
    return out
