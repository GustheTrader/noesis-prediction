"""
Profiler — what the test data actually contains, column by column.

Reads CSV / JSON / JSONL, removes exact duplicate rows (and reports how many),
then gives every column a type and a ROLE:

  identifier   ``*_id`` / ``id`` / ``fooId``       -> candidate entity
  label        ``*_name`` paired with an identifier -> property of that entity
  temporal     dates, ``year``/``season``           -> Season link / index
  flag         booleans, ``is_*`` / ``has_*``        -> property
  prediction   ``predicted_*``, ``edge_*``, ...      -> Prediction node
  target       named by the caller                   -> outcome on the fact
  categorical  few repeated string values            -> candidate node type
  prose        long free text                        -> property, never a node
  measurement  any other number                      -> property

Roles come from name AND values, so a column called ``foo_id`` that holds
floats is a measurement, not an identity.
"""

from __future__ import annotations

import csv
import json
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Optional, Sequence

_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}([T ]\d{2}:\d{2}(:\d{2}(\.\d+)?)?(Z|[+-]\d{2}:?\d{2})?)?$")
_TEMPORAL_NAMES = {"date", "year", "season", "ts", "timestamp", "time", "datetime", "week"}
_PRED_PREFIX = ("predicted_", "pred_", "prob_", "edge_", "expected_")
_PRED_SUFFIX = ("_pred", "_prob", "_edge", "_prediction")


@dataclass
class ColumnProfile:
    name: str
    dtype: str = "empty"          # int | float | bool | date | str | empty
    role: str = "measurement"
    distinct: int = 0
    non_null: int = 0
    examples: list = field(default_factory=list)
    owner_prefix: Optional[str] = None   # "pitcher" for pitcher_era


@dataclass
class DatasetProfile:
    source: str
    raw_rows: int
    rows: list[dict]
    columns: dict[str, ColumnProfile]
    duplicate_rows: int = 0

    @property
    def unique_rows(self) -> int:
        return len(self.rows)

    @property
    def duplication_factor(self) -> float:
        return self.raw_rows / self.unique_rows if self.unique_rows else 0.0

    def by_role(self, role: str) -> list[ColumnProfile]:
        return [c for c in self.columns.values() if c.role == role]


# ---------------------------------------------------------------------------
# Reading
# ---------------------------------------------------------------------------

def _flatten(rec: dict, parent: str = "") -> dict:
    out = {}
    for k, v in rec.items():
        key = f"{parent}_{k}" if parent else str(k)
        if isinstance(v, dict):
            out.update(_flatten(v, key))
        elif isinstance(v, list):
            continue  # lists are not columns
        else:
            out[key] = v
    return out


def read_records(path: str | Path, max_rows: Optional[int] = None) -> list[dict]:
    p = Path(path)
    suffix = p.suffix.lower()
    rows: list[dict] = []
    if suffix in (".csv", ".tsv"):
        with p.open(newline="", encoding="utf-8-sig") as fh:
            reader = csv.DictReader(fh, delimiter="\t" if suffix == ".tsv" else ",")
            for i, r in enumerate(reader):
                if max_rows is not None and i >= max_rows:
                    break
                rows.append(dict(r))
    elif suffix == ".jsonl":
        with p.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                obj = json.loads(line)
                if isinstance(obj, dict):
                    rows.append(_flatten(obj))
                if max_rows is not None and len(rows) >= max_rows:
                    break
    elif suffix == ".json":
        data = json.loads(p.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            # {"games": [...]} or {"id": {...}, ...}
            lists = [v for v in data.values() if isinstance(v, list)]
            if lists:
                data = max(lists, key=len)
            elif all(isinstance(v, dict) for v in data.values()):
                data = list(data.values())
            else:
                data = [data]
        rows = [_flatten(r) for r in data if isinstance(r, dict)]
        if max_rows is not None:
            rows = rows[:max_rows]
    else:
        raise ValueError(f"unsupported file type: {p.name}")
    return rows


def dedupe(rows: Sequence[dict]) -> list[dict]:
    """Drop exact duplicates, keeping first-seen order."""
    seen: set = set()
    out = []
    for r in rows:
        key = tuple(sorted((k, "" if v is None else str(v)) for k, v in r.items()))
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
    return out


# ---------------------------------------------------------------------------
# Typing
# ---------------------------------------------------------------------------

def _is_null(v: Any) -> bool:
    return v is None or (isinstance(v, str) and v.strip() in ("", "null", "None", "NaN", "nan"))


def infer_dtype(values: Iterable[Any]) -> str:
    vals = [v for v in values if not _is_null(v)]
    if not vals:
        return "empty"
    if all(isinstance(v, bool) for v in vals):
        return "bool"
    strs = [str(v).strip() for v in vals]
    lowered = {s.lower() for s in strs}
    if lowered <= {"true", "false"}:
        return "bool"
    if all(re.fullmatch(r"[+-]?\d+", s) for s in strs):
        return "int"
    if all(re.fullmatch(r"[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?", s) for s in strs):
        return "float"
    if all(_DATE.match(s) for s in strs):
        return "date"
    return "str"


def coerce(v: Any, dtype: str) -> Any:
    if _is_null(v):
        return None
    try:
        if dtype == "int":
            return int(str(v).strip())
        if dtype == "float":
            return float(str(v).strip())
        if dtype == "bool":
            return str(v).strip().lower() in ("true", "1")
    except ValueError:
        return v
    return v


def _split_camel_id(name: str) -> Optional[str]:
    """'gameId' -> 'game'; 'pitcher_id' -> 'pitcher'; 'id' -> ''."""
    if name.lower() == "id":
        return ""
    m = re.match(r"^(.+?)_?(id|Id|ID)$", name)
    if m and (name.endswith("_id") or name.endswith("Id") or name.endswith("ID")):
        return m.group(1).lower()
    return None


# ---------------------------------------------------------------------------
# Roles
# ---------------------------------------------------------------------------

def classify(name: str, dtype: str, values: list, rows: int,
             targets: Sequence[str], id_prefixes: set[str]) -> str:
    lname = name.lower()
    if name in targets:
        return "target"
    if lname.startswith(_PRED_PREFIX) or lname.endswith(_PRED_SUFFIX):
        return "prediction"
    if _split_camel_id(name) is not None and dtype in ("int", "str"):
        return "identifier"
    if dtype == "date" or lname in _TEMPORAL_NAMES or lname.endswith(("_date", "_at", "_utc", "_ts")):
        return "temporal"
    if dtype == "bool" or lname.startswith(("is_", "has_")):
        return "flag"
    if dtype == "int":
        distinct = {v for v in values if not _is_null(v)}
        if distinct <= {"0", "1", 0, 1}:
            return "flag"
    if dtype == "str":
        nonnull = [str(v) for v in values if not _is_null(v)]
        if nonnull:
            avg_len = sum(len(s) for s in nonnull) / len(nonnull)
            spaces = sum(s.count(" ") for s in nonnull) / len(nonnull)
            if avg_len > 40 and spaces > 4:
                return "prose"
        prefix = lname[:-5] if lname.endswith("_name") else ("" if lname == "name" else None)
        if prefix is not None and (prefix in id_prefixes or prefix == ""):
            return "label"
        distinct = len(set(nonnull))
        if 1 < distinct <= max(20, int(0.05 * rows)) and distinct < len(nonnull):
            return "categorical"
        return "label" if prefix is not None else "attribute"
    return "measurement"


def profile(path: str | Path, targets: Sequence[str] = (),
            max_rows: Optional[int] = None, rows: Optional[list[dict]] = None) -> DatasetProfile:
    raw = rows if rows is not None else read_records(path, max_rows=max_rows)
    unique = dedupe(raw)
    names: list[str] = []
    for r in unique:
        for k in r:
            if k not in names:
                names.append(k)

    id_prefixes = {p for p in (_split_camel_id(n) for n in names) if p}
    cols: dict[str, ColumnProfile] = {}
    for n in names:
        values = [r.get(n) for r in unique]
        dtype = infer_dtype(values)
        nonnull = [v for v in values if not _is_null(v)]
        cp = ColumnProfile(
            name=n, dtype=dtype,
            role=classify(n, dtype, values, len(unique), targets, id_prefixes),
            distinct=len({str(v) for v in nonnull}),
            non_null=len(nonnull),
            examples=[v for v, _ in Counter(map(str, nonnull)).most_common(3)],
        )
        for pre in sorted(id_prefixes, key=len, reverse=True):
            if n.lower().startswith(pre + "_") and cp.role != "identifier":
                cp.owner_prefix = pre
                break
        cols[n] = cp

    # Coerce values once so downstream dependency checks compare like with like.
    typed = [{k: coerce(v, cols[k].dtype) if k in cols else v for k, v in r.items()}
             for r in unique]
    return DatasetProfile(source=str(path), raw_rows=len(raw), rows=typed,
                          columns=cols, duplicate_rows=len(raw) - len(unique))
