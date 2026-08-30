import subprocess
import tempfile
import unittest
from inspect import signature
from pathlib import Path
from unittest import mock

from codekg.git_history import co_edit_edges
from codekg.parser import scan_repository


class ScanRepositoryTest(unittest.TestCase):
    def test_scan_repository_extracts_nodes_and_edges(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            self._write(repo / "pkg" / "__init__.py", "")
            self._write(repo / "pkg" / "util.py", "def helper():\n    return 1\n")
            self._write(
                repo / "pkg" / "main.py",
                (
                    "from pkg import util\n"
                    "from pkg.util import helper\n\n"
                    "class Greeter:\n"
                    "    def greet(self):\n"
                    "        helper()\n"
                    "        util.helper()\n"
                    "        self._private()\n\n"
                    "    def _private(self):\n"
                    "        return 'ok'\n\n"
                    "def outer():\n"
                    "    def inner():\n"
                    "        return helper()\n"
                    "    return inner()\n"
                ),
            )
            self._write(repo / "notes.txt", "repository note\n")

            graph = scan_repository(repo)

            node_ids = {node.id for node in graph.nodes}
            self.assertIn("file:pkg/main.py", node_ids)
            self.assertIn("file:pkg/util.py", node_ids)
            self.assertIn("file:notes.txt", node_ids)
            self.assertIn("symbol:pkg.main.Greeter", node_ids)
            self.assertIn("symbol:pkg.main.Greeter.greet", node_ids)
            self.assertIn("symbol:pkg.main.Greeter._private", node_ids)
            self.assertIn("symbol:pkg.main.outer", node_ids)
            self.assertIn("symbol:pkg.main.outer.inner", node_ids)
            self.assertIn("symbol:pkg.util.helper", node_ids)

            contains_edges = {
                (edge.src, edge.dst, edge.kind)
                for edge in graph.edges
                if edge.kind == "contains"
            }
            self.assertIn(
                ("file:pkg/main.py", "symbol:pkg.main.Greeter", "contains"),
                contains_edges,
            )
            self.assertIn(
                ("symbol:pkg.main.Greeter", "symbol:pkg.main.Greeter.greet", "contains"),
                contains_edges,
            )
            self.assertIn(
                ("symbol:pkg.main.outer", "symbol:pkg.main.outer.inner", "contains"),
                contains_edges,
            )

            edge_keys = {(edge.src, edge.dst, edge.kind) for edge in graph.edges}
            self.assertIn(
                ("file:pkg/main.py", "file:pkg/util.py", "imports"),
                edge_keys,
            )
            self.assertIn(
                ("symbol:pkg.main.Greeter.greet", "symbol:pkg.util.helper", "calls"),
                edge_keys,
            )
            self.assertIn(
                (
                    "symbol:pkg.main.Greeter.greet",
                    "symbol:pkg.main.Greeter._private",
                    "calls",
                ),
                edge_keys,
            )
            self.assertIn(
                ("symbol:pkg.main.outer.inner", "symbol:pkg.util.helper", "calls"),
                edge_keys,
            )
            self.assertEqual([], graph.warnings)

            sorted_edges = sorted(graph.edges, key=lambda edge: (edge.kind, edge.src, edge.dst))
            self.assertEqual(sorted_edges, graph.edges)

    def test_scan_repository_skips_ignored_dirs_and_records_syntax_errors(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            self._write(repo / "pkg" / "good.py", "def ok():\n    return 1\n")
            self._write(repo / "node_modules" / "skip.py", "def hidden():\n    return 0\n")
            self._write(repo / ".mypy_cache" / "skip.py", "def cached():\n    return 0\n")
            self._write(repo / "build" / "skip.py", "def built():\n    return 0\n")
            self._write(repo / "bad.py", "def broken(:\n    pass\n")

            graph = scan_repository(repo)

            file_paths = {node.path for node in graph.nodes if node.kind == "file"}
            self.assertIn("pkg/good.py", file_paths)
            self.assertIn("bad.py", file_paths)
            self.assertNotIn("node_modules/skip.py", file_paths)
            self.assertNotIn(".mypy_cache/skip.py", file_paths)
            self.assertNotIn("build/skip.py", file_paths)
            self.assertTrue(any("bad.py" in warning for warning in graph.warnings))

    def test_scan_repository_resolves_relative_imports(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            self._write(repo / "pkg" / "__init__.py", "")
            self._write(repo / "pkg" / "helpers.py", "def local_helper():\n    return 1\n")
            self._write(
                repo / "pkg" / "consumer.py",
                (
                    "from .helpers import local_helper\n\n"
                    "def use_helper():\n"
                    "    return local_helper()\n"
                ),
            )

            graph = scan_repository(repo)
            edge_keys = {(edge.src, edge.dst, edge.kind) for edge in graph.edges}

            self.assertIn(
                ("file:pkg/consumer.py", "file:pkg/helpers.py", "imports"),
                edge_keys,
            )
            self.assertIn(
                ("symbol:pkg.consumer.use_helper", "symbol:pkg.helpers.local_helper", "calls"),
                edge_keys,
            )

    def test_scan_repository_keeps_arbitrary_readable_non_python_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            self._write(repo / "assets" / "schema.customext", "name: value\n")

            graph = scan_repository(repo)

            nodes_by_id = {node.id: node for node in graph.nodes}
            file_node = nodes_by_id["file:assets/schema.customext"]
            self.assertEqual("file", file_node.kind)
            self.assertEqual("assets/schema.customext", file_node.path)
            self.assertEqual("name: value\n", file_node.text)

    def test_scan_repository_handles_long_utf8_python_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            prefix = "# " + ("é" * 100_001) + "\n"
            self._write(
                repo / "pkg" / "long_module.py",
                prefix + "def trailing_symbol():\n    return 'ok'\n",
            )

            graph = scan_repository(repo)

            nodes_by_id = {node.id: node for node in graph.nodes}
            self.assertIn("file:pkg/long_module.py", nodes_by_id)
            self.assertIn("symbol:pkg.long_module.trailing_symbol", nodes_by_id)
            self.assertTrue(nodes_by_id["file:pkg/long_module.py"].text.endswith("é"))
            self.assertEqual([], graph.warnings)

    def test_scan_repository_records_oserror_warning_and_continues(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            self._write(repo / "ok.py", "def fine():\n    return 1\n")
            failing_path = repo / "broken.txt"
            self._write(failing_path, "ignored\n")

            original_open = Path.open

            def fake_open(path_obj: Path, *args, **kwargs):
                if path_obj == failing_path and "rb" in args:
                    raise OSError("simulated read failure")
                return original_open(path_obj, *args, **kwargs)

            with mock.patch.object(Path, "open", autospec=True, side_effect=fake_open):
                graph = scan_repository(repo)

            file_paths = {node.path for node in graph.nodes if node.kind == "file"}
            self.assertIn("ok.py", file_paths)
            self.assertNotIn("broken.txt", file_paths)
            self.assertTrue(any("broken.txt" in warning for warning in graph.warnings))

    def test_scan_repository_records_invalid_utf8_warning_for_non_python_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            self._write(repo / "ok.py", "def fine():\n    return 1\n")
            invalid_path = repo / "broken.bintext"
            invalid_path.write_bytes(b"\xff\xfehello")

            graph = scan_repository(repo)

            nodes_by_id = {node.id: node for node in graph.nodes}
            self.assertIn("file:broken.bintext", nodes_by_id)
            self.assertIn("file:ok.py", nodes_by_id)
            self.assertIn("\ufffd", nodes_by_id["file:broken.bintext"].text)
            self.assertTrue(
                any(
                    "broken.bintext" in warning and "UnicodeDecodeError" in warning
                    for warning in graph.warnings
                )
            )

    def test_scan_repository_records_directory_walk_warning_and_continues(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            self._write(repo / "pkg" / "ok.py", "def fine():\n    return 1\n")
            blocked_dir = repo / "blocked"
            self._write(blocked_dir / "hidden.py", "def hidden():\n    return 1\n")

            original_iterdir = Path.iterdir

            def fake_iterdir(path_obj: Path):
                if path_obj == blocked_dir:
                    raise OSError("simulated walk failure")
                return original_iterdir(path_obj)

            with mock.patch.object(Path, "iterdir", autospec=True, side_effect=fake_iterdir):
                graph = scan_repository(repo)

            file_paths = {node.path for node in graph.nodes if node.kind == "file"}
            self.assertIn("pkg/ok.py", file_paths)
            self.assertNotIn("blocked/hidden.py", file_paths)
            self.assertTrue(any("blocked" in warning for warning in graph.warnings))

    @staticmethod
    def _write(path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


class CoEditEdgesTest(unittest.TestCase):
    def test_co_edit_edges_public_signature_is_stable(self):
        self.assertEqual(
            ["repo_root", "max_commits", "max_files_per_commit"],
            list(signature(co_edit_edges).parameters),
        )

    def test_co_edit_edges_counts_pairs_deterministically(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            self._init_git_repo(repo)
            self._commit_files(
                repo,
                {
                    "a.py": "print('a1')\n",
                    "b.py": "print('b1')\n",
                },
                "initial pair",
            )
            self._commit_files(
                repo,
                {
                    "a.py": "print('a2')\n",
                    "b.py": "print('b2')\n",
                },
                "repeat pair",
            )
            self._commit_files(
                repo,
                {
                    "b.py": "print('b3')\n",
                    "c.py": "print('c1')\n",
                },
                "second pair",
            )
            self._commit_files(
                repo,
                {
                    "a.py": "print('a4')\n",
                    "b.py": "print('b4')\n",
                    "c.py": "print('c4')\n",
                    "d.py": "print('d4')\n",
                },
                "oversized commit",
            )

            edges = co_edit_edges(
                repo,
                max_commits=10,
                max_files_per_commit=3,
            )

            self.assertEqual(
                [
                    ("file:a.py", "file:b.py", "co_edit", 2.0),
                    ("file:b.py", "file:c.py", "co_edit", 1.0),
                ],
                [(edge.src, edge.dst, edge.kind, edge.weight) for edge in edges],
            )

    def test_co_edit_edges_returns_empty_for_non_git_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            edges = co_edit_edges(Path(tmpdir), max_commits=5, max_files_per_commit=5)
            self.assertEqual([], edges)

    @staticmethod
    def _init_git_repo(repo: Path) -> None:
        subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.name", "Task Worker"],
            cwd=repo,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.email", "task@example.com"],
            cwd=repo,
            check=True,
            capture_output=True,
        )

    @classmethod
    def _commit_files(cls, repo: Path, files: dict[str, str], message: str) -> None:
        for relative_path, content in files.items():
            cls._write(repo / relative_path, content)
        subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", message],
            cwd=repo,
            check=True,
            capture_output=True,
        )

    @staticmethod
    def _write(path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
