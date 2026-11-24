"""
Data agent regressions. Run:  python -m unittest discover data_agent/tests
(no pytest or Neo4j needed). Each test pins a way the proposal could be wrong.
"""

from __future__ import annotations

import csv
import json
import os
import tempfile
import unittest
from pathlib import Path

from data_agent import DataAgent
from data_agent.emit import ddl, load_template, markdown
from data_agent.graph_source import (GraphLabel, GraphRelation, GraphSnapshot, Neo4jConfig,
                                     from_cypher_files, from_neo4j, load_snapshot)
from data_agent.ontology import infer, stability
from data_agent.profiler import infer_dtype, profile

REPO = Path(__file__).resolve().parents[2]
TEST_CSV = REPO / "mlb_first5" / "data" / "processed" / "test_data.csv"


def nfl_graph() -> GraphSnapshot:
    """The shape of the real GNOESIS graph: NFL base labels + a CFB_ domain."""
    g = GraphSnapshot(origin="fixture")
    g.labels["Team"] = GraphLabel("Team", unique_keys=["code"], props=["name"])
    g.labels["Game"] = GraphLabel("Game", unique_keys=["gameId"])
    g.labels["Season"] = GraphLabel("Season", unique_keys=["year"])
    g.labels["CFB_Game"] = GraphLabel("CFB_Game")
    g.labels["CFB_Team"] = GraphLabel("CFB_Team")
    for r in ("IN_GAME", "IN_SEASON", "HOME_TEAM", "AWAY_TEAM"):
        g.relations[r] = GraphRelation(r)
    return g


def synthetic_rows(dupes: int = 1) -> list[dict]:
    """3 seasons x 10 pitchers x 4 starts. Known ground truth:
    name stable per pitcher; era + team fixed per pitcher-season; runs per game."""
    rows = []
    event = 1000
    for year in (2021, 2022, 2023):
        for start in range(4):
            for pair in range(5):
                event += 1
                for side in (0, 1):
                    pid = pair * 2 + side
                    rows.append({
                        "pitcher_id": str(100 + pid),
                        "pitcher_name": f"Pitcher {pid}",
                        "pitcher_era": f"{2.5 + pid * 0.1 + (year - 2021) * 0.3:.2f}",
                        "team_id": str((pid + year) % 12 + 1),
                        "event_id": str(event),
                        "date": f"{year}-05-{start + 1:02d}",
                        "year": str(year),
                        "is_home": str(side),
                        "first_5_runs_allowed": str((pid + start + year) % 5),
                        "predicted_f5": f"{1 + (pid % 3) * 0.5:.2f}",
                        "pitcher_days_rest": "",
                    })
    return rows * dupes


def write_csv(rows: list[dict], path: Path) -> Path:
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    return path


def run(rows, graph=None, domain="MLB"):
    p = profile("fixture.csv", targets=["first_5_runs_allowed"], rows=rows)
    return infer(p, graph if graph is not None else nfl_graph(), domain=domain)


def prop_home(proposal, column):
    for e in proposal.entities:
        for pm in e.props:
            if pm.column == column:
                return ("node", e.label, pm.evidence)
    for r in proposal.relations:
        for pm in r.props:
            if pm.column == column:
                return (r.type, f"{r.src}->{r.dst}", pm.evidence)
    return None


class ProfilerTests(unittest.TestCase):
    def test_duplicate_rows_are_removed_and_reported(self):
        p = run(synthetic_rows(dupes=50))
        self.assertEqual(p.unique_rows, 120)
        self.assertEqual(p.raw_rows, 6000)
        self.assertTrue(any(f.severity == "high" and "duplicates" in f.message for f in p.findings))

    def test_dtypes(self):
        self.assertEqual(infer_dtype(["1", "2"]), "int")
        self.assertEqual(infer_dtype(["1.5", "2"]), "float")
        self.assertEqual(infer_dtype(["2025-03-27", ""]), "date")
        self.assertEqual(infer_dtype(["true", "False"]), "bool")
        self.assertEqual(infer_dtype(["", None]), "empty")

    def test_float_valued_id_column_is_not_an_identity(self):
        rows = [{"x_id": f"{i}.5", "v": str(i)} for i in range(10)]
        self.assertNotEqual(profile("f", rows=rows).columns["x_id"].role, "identifier")

    def test_prose_is_never_a_node_type(self):
        rows = [{"thing_id": str(i % 3),
                 "note": "the starter looked sharp early but tired badly in the fourth"}
                for i in range(30)]
        p = run(rows, domain=None)
        self.assertNotIn("Note", [e.concept for e in p.entities])


class GrainTests(unittest.TestCase):
    def setUp(self):
        self.p = run(synthetic_rows())

    def test_stable_column_becomes_node_property(self):
        self.assertEqual(prop_home(self.p, "pitcher_name"), ("node", "Pitcher", "stable"))

    def test_season_stable_column_lives_on_in_season(self):
        home = prop_home(self.p, "pitcher_era")
        self.assertEqual(home[0], "IN_SEASON")
        self.assertEqual(home[2], "season")

    def test_per_game_column_lives_on_in_game(self):
        home = prop_home(self.p, "first_5_runs_allowed")
        self.assertEqual(home[0], "IN_GAME")
        self.assertEqual(home[1], "Pitcher->MLB_Game")

    def test_membership_is_season_scoped(self):
        rel = next(r for r in self.p.relations if r.type == "PITCHER_OF")
        self.assertEqual(rel.dst, "MLB_Team")
        self.assertEqual([pm.prop for pm in rel.props], ["season"])

    def test_missing_values_are_not_evidence(self):
        rows = [{"k": "a", "v": None}, {"k": "a", "v": None}, {"k": "a", "v": 1}]
        self.assertEqual(stability(rows * 1, ["k"], "v"), (None, 0))

    def test_ids_seen_once_prove_nothing(self):
        rows = [r for i, r in enumerate(synthetic_rows()) if r["year"] == "2021"
                and r["date"].endswith("01")]           # every pitcher once
        p = run(rows)
        self.assertEqual(prop_home(p, "pitcher_era")[2], "unproven")
        self.assertTrue(any(f.severity == "info" for f in p.findings))


class AlignmentTests(unittest.TestCase):
    def test_clashing_key_is_scoped_by_domain_following_precedent(self):
        p = run(synthetic_rows())
        team = p.entity("Team")
        self.assertEqual((team.status, team.label), ("RENAMED", "MLB_Team"))
        self.assertIn("CFB_Team", team.reason)
        self.assertEqual(p.entity("Game").label, "MLB_Game")

    def test_clash_without_domain_is_refused_not_guessed(self):
        p = run(synthetic_rows(), domain=None)
        self.assertEqual(p.entity("Team").status, "UNRESOLVED")
        self.assertNotIn("FOR (n:`Team`)", ddl(p))
        self.assertIn("UNRESOLVED Team", ddl(p))

    def test_season_is_reused(self):
        s = run(synthetic_rows()).entity("Season")
        self.assertEqual((s.status, s.label, s.key_prop), ("REUSE", "Season", "year"))

    def test_existing_relation_names_are_reused(self):
        types = {r.type: r.status for r in run(synthetic_rows()).relations}
        self.assertEqual(types["IN_GAME"], "REUSE")
        self.assertEqual(types["IN_SEASON"], "REUSE")
        self.assertEqual(types["PREDICTS"], "NEW")

    def test_existing_domain_label_is_reused(self):
        g = nfl_graph()
        g.labels["MLB_Team"] = GraphLabel("MLB_Team", unique_keys=["teamId"])
        self.assertEqual(run(synthetic_rows(), g).entity("Team").status, "REUSE")

    def test_live_key_samples_catch_a_type_clash_behind_a_matching_name(self):
        g = nfl_graph()
        g.labels["Team"] = GraphLabel("Team", unique_keys=["teamId"],
                                      key_samples={"teamId": ["KC", "SF", "BUF"]})
        team = run(synthetic_rows(), g).entity("Team")
        self.assertEqual(team.status, "RENAMED")
        self.assertIn("str", team.reason)

    def test_no_graph_reports_everything_new_and_says_so(self):
        p = run(synthetic_rows(), GraphSnapshot())
        self.assertTrue(all(e.status == "NEW" for e in p.entities))
        self.assertTrue(any("No graph" in f.message for f in p.findings))


class EmitTests(unittest.TestCase):
    def setUp(self):
        self.p = run(synthetic_rows())

    def test_ddl_is_idempotent_and_non_destructive(self):
        text = ddl(self.p)
        statements = [l for l in text.splitlines() if l and not l.startswith("//")]
        self.assertTrue(statements)
        for s in statements:
            self.assertIn("IF NOT EXISTS", s)
            for bad in ("DROP", "DELETE", "DETACH", " SET "):
                self.assertNotIn(bad, s.upper())

    def test_reused_labels_get_no_ddl(self):
        self.assertNotIn("(n:`Season`)", ddl(self.p))

    def test_load_template_uses_proposed_labels_and_prediction(self):
        t = load_template(self.p)
        self.assertIn("MERGE (n0:`Pitcher` {`pitcherId`: row.`pitcher_id`})", t)
        self.assertIn(":`MLB_Game`", t)
        self.assertIn("MERGE (pr)-[:PREDICTS]->", t)
        self.assertNotIn(":`Team` ", t)

    def test_markdown_lists_every_column(self):
        md = markdown(self.p)
        for col in synthetic_rows()[0]:
            self.assertIn(f"`{col}`", md)


class GraphSourceTests(unittest.TestCase):
    def test_unconfigured_neo4j_is_an_error_not_an_exception(self):
        snap = from_neo4j(Neo4jConfig(uri=None, password=None))
        self.assertTrue(snap.empty)
        self.assertIn("NEO4J_URI", snap.error)

    def test_cypher_parser_keeps_labels_verbatim(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d, "s.cypher").write_text(
                "CREATE CONSTRAINT g IF NOT EXISTS FOR (g:CFB_Game) REQUIRE g.gameId IS UNIQUE;\n"
                "MATCH (a:CFB_Team)-[:HOME_TEAM]->(g:CFB_Game) RETURN a", encoding="utf-8")
            snap = from_cypher_files([d])
        self.assertIn("CFB_Game", snap.labels)
        self.assertNotIn("CFBGame", snap.labels)
        self.assertEqual(snap.labels["CFB_Game"].unique_keys, ["gameId"])
        self.assertIn("HOME_TEAM", snap.relations)

    def test_gnoesis_snapshot_format_loads(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d, "g.json")
            path.write_text(json.dumps({"origin": "cypher", "nodes": {
                "Team": {"name": "Team", "props": ["name"], "unique_keys": ["code"],
                         "indexed": [], "sources": ["x.cypher"]}},
                "relations": {"IN_SEASON": {"name": "IN_SEASON", "sources": []}}}))
            snap = load_snapshot(path)
        self.assertEqual(snap.labels["Team"].key, "code")
        self.assertIn("IN_SEASON", snap.relations)


class AgentTests(unittest.TestCase):
    def test_end_to_end_from_files(self):
        with tempfile.TemporaryDirectory() as d:
            csv_path = write_csv(synthetic_rows(dupes=3), Path(d, "t.csv"))
            agent = DataAgent(domain="MLB")
            agent.graph = nfl_graph()
            agent.ingest_data([csv_path])
            files = agent.write(Path(d, "out"))
            for f in files.values():
                self.assertTrue(f.exists() and f.stat().st_size > 0)
            self.assertIn("RENAMED", agent.summary())

    def test_ingest_graph_without_sources_explains_itself(self):
        env = {k: os.environ.pop(k) for k in ("NEO4J_URI", "NEO4J_PASSWORD") if k in os.environ}
        try:
            agent = DataAgent()
            agent.ingest_graph()
            self.assertIn("no graph source", agent.graph.error)
        finally:
            os.environ.update(env)

    @unittest.skipUnless(TEST_CSV.exists(), "repo test data not present")
    def test_real_test_data(self):
        agent = DataAgent(domain="MLB")
        agent.graph = nfl_graph()
        agent.ingest_data([TEST_CSV])
        p = agent.propose()
        self.assertEqual(p.unique_rows, 100)               # 12,900 raw rows, ~129x duplication
        self.assertEqual(p.entity("Game").label, "MLB_Game")
        self.assertTrue(p.entity("Pitcher").is_subject)
        self.assertEqual(prop_home(p, "pitcher_name")[0], "node")


if __name__ == "__main__":
    unittest.main()
