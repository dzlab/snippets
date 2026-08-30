import tempfile
import unittest
from pathlib import Path

from codekg.model import Edge, Node, ParsedGraph
from codekg.retrieval import (
    graph_rank,
    lexical_rank,
    ndcg_at_k,
    recall_at_k,
    structure_map_markdown,
    tokenize_identifier,
)
from codekg.store import counts, load_file_graph, open_store, replace_graph


def sample_graph() -> ParsedGraph:
    return ParsedGraph(
        nodes=[
            Node(
                id="file:api.py",
                kind="file",
                path="api.py",
                name="api.py",
                text="API endpoint calls the service layer.",
            ),
            Node(
                id="file:database.py",
                kind="file",
                path="database.py",
                name="database.py",
                text="Database access for persistent storage.",
            ),
            Node(
                id="file:service.py",
                kind="file",
                path="service.py",
                name="service.py",
                text="Service layer logic for the API.",
            ),
            Node(
                id="file:test_api.py",
                kind="file",
                path="test_api.py",
                name="test_api.py",
                text="Tests for the API endpoint.",
            ),
            Node(
                id="symbol:api.handle_request",
                kind="function",
                path="api.py",
                name="api.handle_request",
            ),
            Node(
                id="symbol:service.fetch_user",
                kind="function",
                path="service.py",
                name="service.fetch_user",
            ),
            Node(
                id="symbol:database.query_db",
                kind="function",
                path="database.py",
                name="database.query_db",
            ),
        ],
        edges=[
            Edge("file:api.py", "symbol:api.handle_request", "contains"),
            Edge("file:service.py", "symbol:service.fetch_user", "contains"),
            Edge("file:database.py", "symbol:database.query_db", "contains"),
            Edge("file:api.py", "file:service.py", "imports"),
            Edge("file:service.py", "file:database.py", "imports"),
            Edge("symbol:api.handle_request", "symbol:service.fetch_user", "calls"),
            Edge("symbol:service.fetch_user", "symbol:database.query_db", "calls"),
            Edge("file:test_api.py", "file:api.py", "co_edit", weight=1.0),
        ],
        warnings=[],
    )


class StoreRoundTripTest(unittest.TestCase):
    def test_replace_graph_and_load_file_graph_round_trip(self):
        graph = sample_graph()

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "graph.sqlite3"
            conn = open_store(db_path)
            self.addCleanup(conn.close)

            replace_graph(conn, graph)

            self.assertEqual({"nodes": 7, "edges": 8}, counts(conn))

            file_graph = load_file_graph(conn)

        self.assertEqual(
            ["api.py", "database.py", "service.py", "test_api.py"],
            [node.path for node in file_graph.nodes],
        )
        self.assertEqual(
            {
                "api.py": ["service.py", "test_api.py"],
                "database.py": ["service.py"],
                "service.py": ["api.py", "database.py"],
                "test_api.py": ["api.py"],
            },
            file_graph.adjacency,
        )
        self.assertEqual(("call", "import"), file_graph.edge_labels[("api.py", "service.py")])
        self.assertEqual(
            ("call", "import"),
            file_graph.edge_labels[("service.py", "database.py")],
        )
        self.assertEqual(("co_edit",), file_graph.edge_labels[("api.py", "test_api.py")])
        self.assertNotIn(("api.py", "api.py"), file_graph.edge_labels)

    def test_replace_graph_replaces_existing_rows_in_one_store(self):
        first_graph = sample_graph()
        second_graph = ParsedGraph(
            nodes=[
                Node(
                    id="file:solo.py",
                    kind="file",
                    path="solo.py",
                    name="solo.py",
                    text="single file",
                ),
            ],
            edges=[],
            warnings=[],
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "graph.sqlite3"
            conn = open_store(db_path)
            self.addCleanup(conn.close)

            replace_graph(conn, first_graph)
            replace_graph(conn, second_graph)

            self.assertEqual({"nodes": 1, "edges": 0}, counts(conn))
            self.assertEqual(["solo.py"], [node.path for node in load_file_graph(conn).nodes])

    def test_load_file_graph_handles_empty_store(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "graph.sqlite3"
            conn = open_store(db_path)
            self.addCleanup(conn.close)

            file_graph = load_file_graph(conn)

        self.assertEqual([], file_graph.nodes)
        self.assertEqual({}, file_graph.adjacency)
        self.assertEqual({}, file_graph.edge_labels)


class RetrievalTest(unittest.TestCase):
    def test_tokenize_identifier_splits_snake_case_and_paths(self):
        self.assertEqual(
            ["pkg", "test", "api", "handler", "py"],
            tokenize_identifier("pkg/test_api-handler.py"),
        )

    def test_lexical_rank_prefers_query_overlap_and_breaks_ties_by_path(self):
        graph = sample_graph()

        with tempfile.TemporaryDirectory() as tmpdir:
            conn = open_store(Path(tmpdir) / "graph.sqlite3")
            self.addCleanup(conn.close)
            replace_graph(conn, graph)
            file_graph = load_file_graph(conn)

        self.assertEqual(
            ["api.py", "test_api.py", "service.py", "database.py"],
            lexical_rank("api endpoint", file_graph).items,
        )

        tied_graph = ParsedGraph(
            nodes=[
                Node("file:b.py", "file", "b.py", "b.py", "helper text"),
                Node("file:a.py", "file", "a.py", "a.py", "helper text"),
            ],
            edges=[],
            warnings=[],
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            conn = open_store(Path(tmpdir) / "ties.sqlite3")
            self.addCleanup(conn.close)
            replace_graph(conn, tied_graph)
            tied_file_graph = load_file_graph(conn)

        self.assertEqual(
            ["a.py", "b.py"],
            lexical_rank("helper", tied_file_graph).items,
        )

    def test_graph_rank_reaches_multi_hop_and_handles_dangling_nodes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            conn = open_store(Path(tmpdir) / "graph.sqlite3")
            self.addCleanup(conn.close)
            replace_graph(conn, sample_graph())
            file_graph = load_file_graph(conn)

        lexical = lexical_rank("api endpoint", file_graph)
        ranked = graph_rank("api endpoint", file_graph, n_anchors=1)

        self.assertEqual("api.py", lexical.items[0])
        self.assertIn("database.py", ranked.items[:3])
        self.assertGreater(
            ranked.scores[ranked.items.index("database.py")],
            ranked.scores[ranked.items.index("test_api.py")],
        )

        dangling_graph = ParsedGraph(
            nodes=[
                Node("file:anchor.py", "file", "anchor.py", "anchor.py", "anchor"),
                Node("file:isolated.py", "file", "isolated.py", "isolated.py", "isolated"),
            ],
            edges=[],
            warnings=[],
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            conn = open_store(Path(tmpdir) / "dangling.sqlite3")
            self.addCleanup(conn.close)
            replace_graph(conn, dangling_graph)
            dangling_file_graph = load_file_graph(conn)

        self.assertEqual(
            ["anchor.py", "isolated.py"],
            graph_rank("anchor", dangling_file_graph, n_anchors=1).items,
        )

    def test_metrics_and_structure_map(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            conn = open_store(Path(tmpdir) / "graph.sqlite3")
            self.addCleanup(conn.close)
            replace_graph(conn, sample_graph())
            file_graph = load_file_graph(conn)

        ranked = graph_rank("api endpoint", file_graph, n_anchors=1)
        self.assertEqual(1.0, recall_at_k(["api.py", "database.py"], ["database.py"], 2))
        self.assertAlmostEqual(
            1.0,
            ndcg_at_k(["api.py", "database.py"], ["api.py", "database.py"], 2),
        )

        markdown = structure_map_markdown(
            "api `endpoint`",
            file_graph,
            ["api.py", "service.py", "database.py"],
            max_files=3,
            max_neighbors_per_kind=2,
        )

        self.assertIn("Query: `api \\`endpoint\\``", markdown)
        self.assertIn("Anchors: `api.py`", markdown)
        self.assertIn("Selected Files: `api.py`, `service.py`, `database.py`", markdown)
        self.assertIn("- imports: `service.py`", markdown)
        self.assertIn("- calls: `api.py`, `database.py`", markdown)
        self.assertIn("- co_edit: `test_api.py`", markdown)


if __name__ == "__main__":
    unittest.main()
