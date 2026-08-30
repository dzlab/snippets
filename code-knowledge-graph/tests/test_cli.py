import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class CliIntegrationTest(unittest.TestCase):
    def test_cli_index_retrieve_map_experiment_and_ab_dry_run(self):
        project_root = Path(__file__).resolve().parents[1]

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            repo_path = tmp_path / "repo"
            db_path = tmp_path / "graph.sqlite3"
            tasks_path = tmp_path / "tasks.json"

            self._init_repo(repo_path)
            tasks_path.write_text(
                json.dumps(
                    [
                        {
                            "query": "Which file defines helper_value?",
                            "gold_files": ["pkg/helpers.py"],
                        }
                    ]
                ),
                encoding="utf-8",
            )

            index_result = self._run_cli(
                project_root,
                "index",
                str(repo_path),
                "--db",
                str(db_path),
                "--max-commits",
                "10",
                "--max-files-per-commit",
                "10",
            )
            self.assertEqual(0, index_result.returncode, index_result.stderr)
            index_payload = json.loads(index_result.stdout)
            self.assertGreater(index_payload["counts"]["nodes"], 0)
            self.assertGreater(index_payload["counts"]["edges"], 0)
            self.assertEqual([], index_payload["warnings"])

            retrieve_result = self._run_cli(
                project_root,
                "retrieve",
                "--db",
                str(db_path),
                "--query",
                "defines helper_value",
                "--k",
                "2",
                "--anchors",
                "1",
            )
            self.assertEqual(0, retrieve_result.returncode, retrieve_result.stderr)
            retrieve_payload = json.loads(retrieve_result.stdout)
            self.assertEqual(["pkg/helpers.py"], retrieve_payload["anchors"])
            self.assertEqual("pkg/helpers.py", retrieve_payload["lexical"]["items"][0])
            self.assertEqual(2, len(retrieve_payload["graph"]["items"]))

            map_result = self._run_cli(
                project_root,
                "map",
                "--db",
                str(db_path),
                "--query",
                "defines helper_value",
                "--k",
                "2",
                "--anchors",
                "1",
            )
            self.assertEqual(0, map_result.returncode, map_result.stderr)
            self.assertIn("### `pkg/helpers.py`", map_result.stdout)
            self.assertIn("Anchors: `pkg/helpers.py`", map_result.stdout)

            experiment_result = self._run_cli(
                project_root,
                "experiment",
                "--db",
                str(db_path),
                "--tasks",
                str(tasks_path),
            )
            self.assertEqual(0, experiment_result.returncode, experiment_result.stderr)
            experiment_payload = json.loads(experiment_result.stdout)
            task_payload = experiment_payload["tasks"][0]
            self.assertIn("recall_at_1", task_payload["lexical"])
            self.assertIn("recall_at_3", task_payload["lexical"])
            self.assertIn("recall_at_5", task_payload["lexical"])
            self.assertIn("recall_at_1", task_payload["graph"])
            self.assertIn("recall_at_3", task_payload["graph"])
            self.assertIn("recall_at_5", task_payload["graph"])
            self.assertIn("recall_at_1", experiment_payload["aggregate"]["lexical"])
            self.assertIn("recall_at_5", experiment_payload["aggregate"]["graph"])

            ab_result = self._run_cli(
                project_root,
                "ab",
                "--db",
                str(db_path),
                "--tasks",
                str(tasks_path),
                "--base-url",
                "http://127.0.0.1:9999",
                "--model",
                "local-model",
                "--dry-run",
                "--runs",
                "1",
                "--seed",
                "7",
                "--k",
                "2",
            )
            self.assertEqual(0, ab_result.returncode, ab_result.stderr)
            ab_payload = json.loads(ab_result.stdout)
            self.assertEqual(2, len(ab_payload["records"]))
            self.assertEqual(
                ["control", "treatment"],
                [record["arm"] for record in ab_payload["records"]],
            )
            self.assertEqual([], ab_payload["records"][0]["ranked_files"])
            self.assertEqual([], ab_payload["records"][1]["ranked_files"])
            self.assertIsNone(ab_payload["records"][0]["error"])
            self.assertIsNone(ab_payload["records"][1]["error"])

    def test_retrieve_requires_existing_db_and_non_empty_query(self):
        project_root = Path(__file__).resolve().parents[1]

        with tempfile.TemporaryDirectory() as tmpdir:
            missing_db = Path(tmpdir) / "missing.sqlite3"

            missing_db_result = self._run_cli(
                project_root,
                "retrieve",
                "--db",
                str(missing_db),
                "--query",
                "helper",
            )
            self.assertNotEqual(0, missing_db_result.returncode)
            self.assertIn("db", missing_db_result.stderr.lower())

            empty_query_result = self._run_cli(
                project_root,
                "retrieve",
                "--db",
                str(project_root / "placeholder.sqlite3"),
                "--query",
                "   ",
            )
            self.assertNotEqual(0, empty_query_result.returncode)
            self.assertIn("query", empty_query_result.stderr.lower())

    def test_index_warns_when_git_history_is_unavailable(self):
        project_root = Path(__file__).resolve().parents[1]

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            repo_path = tmp_path / "repo"
            db_path = tmp_path / "graph.sqlite3"

            (repo_path / "pkg").mkdir(parents=True)
            (repo_path / "pkg" / "module.py").write_text(
                "def helper_value():\n    return 7\n",
                encoding="utf-8",
            )

            result = self._run_cli(
                project_root,
                "index",
                str(repo_path),
                "--db",
                str(db_path),
            )

            self.assertEqual(0, result.returncode, result.stderr)
            payload = json.loads(result.stdout)
            self.assertGreater(payload["counts"]["nodes"], 0)
            self.assertTrue(
                any("git co-edit history unavailable" in warning for warning in payload["warnings"])
            )

    def test_experiment_rejects_missing_gold_files_key(self):
        project_root = Path(__file__).resolve().parents[1]

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            repo_path = tmp_path / "repo"
            db_path = tmp_path / "graph.sqlite3"
            tasks_path = tmp_path / "tasks.json"

            self._init_repo(repo_path)
            self._index_repo(project_root, repo_path, db_path)
            tasks_path.write_text(
                json.dumps([{"query": "Which file defines helper_value?"}]),
                encoding="utf-8",
            )

            result = self._run_cli(
                project_root,
                "experiment",
                "--db",
                str(db_path),
                "--tasks",
                str(tasks_path),
            )

            self.assertNotEqual(0, result.returncode)
            self.assertIn("gold_files", result.stderr)

    def test_experiment_rejects_invalid_gold_file_path(self):
        project_root = Path(__file__).resolve().parents[1]

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            repo_path = tmp_path / "repo"
            db_path = tmp_path / "graph.sqlite3"
            tasks_path = tmp_path / "tasks.json"

            self._init_repo(repo_path)
            self._index_repo(project_root, repo_path, db_path)
            tasks_path.write_text(
                json.dumps(
                    [
                        {
                            "query": "Which file defines helper_value?",
                            "gold_files": ["/tmp/pkg/helpers.py"],
                        }
                    ]
                ),
                encoding="utf-8",
            )

            result = self._run_cli(
                project_root,
                "experiment",
                "--db",
                str(db_path),
                "--tasks",
                str(tasks_path),
            )

            self.assertNotEqual(0, result.returncode)
            self.assertIn("gold_files", result.stderr)
            self.assertIn("/tmp/pkg/helpers.py", result.stderr)

    def test_experiment_rejects_gold_file_missing_from_index(self):
        project_root = Path(__file__).resolve().parents[1]

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            repo_path = tmp_path / "repo"
            db_path = tmp_path / "graph.sqlite3"
            tasks_path = tmp_path / "tasks.json"

            self._init_repo(repo_path)
            self._index_repo(project_root, repo_path, db_path)
            tasks_path.write_text(
                json.dumps(
                    [
                        {
                            "query": "Which file defines helper_value?",
                            "gold_files": ["pkg/missing.py"],
                        }
                    ]
                ),
                encoding="utf-8",
            )

            result = self._run_cli(
                project_root,
                "experiment",
                "--db",
                str(db_path),
                "--tasks",
                str(tasks_path),
            )

            self.assertNotEqual(0, result.returncode)
            self.assertIn("task 0", result.stderr)
            self.assertIn("pkg/missing.py", result.stderr)

    def test_ab_rejects_unindexed_gold_file_and_output_write_errors(self):
        project_root = Path(__file__).resolve().parents[1]

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            repo_path = tmp_path / "repo"
            db_path = tmp_path / "graph.sqlite3"
            tasks_path = tmp_path / "tasks.json"
            output_dir = tmp_path / "output-dir"

            self._init_repo(repo_path)
            self._index_repo(project_root, repo_path, db_path)

            tasks_path.write_text(
                json.dumps(
                    [
                        {
                            "query": "Which file defines helper_value?",
                            "gold_files": ["pkg/missing.py"],
                        }
                    ]
                ),
                encoding="utf-8",
            )
            output_dir.mkdir()

            missing_gold_result = self._run_cli(
                project_root,
                "ab",
                "--db",
                str(db_path),
                "--tasks",
                str(tasks_path),
                "--base-url",
                "http://127.0.0.1:9999",
                "--model",
                "local-model",
                "--dry-run",
            )

            self.assertNotEqual(0, missing_gold_result.returncode)
            self.assertIn("pkg/missing.py", missing_gold_result.stderr)

            tasks_path.write_text(
                json.dumps(
                    [
                        {
                            "query": "Which file defines helper_value?",
                            "gold_files": ["pkg/helpers.py"],
                        }
                    ]
                ),
                encoding="utf-8",
            )

            output_error_result = self._run_cli(
                project_root,
                "ab",
                "--db",
                str(db_path),
                "--tasks",
                str(tasks_path),
                "--base-url",
                "http://127.0.0.1:9999",
                "--model",
                "local-model",
                "--dry-run",
                "--output",
                str(output_dir),
            )

            self.assertNotEqual(0, output_error_result.returncode)
            self.assertIn("output", output_error_result.stderr.lower())
            self.assertNotIn("Traceback", output_error_result.stderr)

    def _run_cli(self, project_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-m", "codekg", *args],
            cwd=project_root,
            check=False,
            capture_output=True,
            text=True,
        )

    def _index_repo(self, project_root: Path, repo_path: Path, db_path: Path) -> None:
        result = self._run_cli(
            project_root,
            "index",
            str(repo_path),
            "--db",
            str(db_path),
            "--max-commits",
            "10",
            "--max-files-per-commit",
            "10",
        )
        self.assertEqual(0, result.returncode, result.stderr)

    def _init_repo(self, repo_path: Path) -> None:
        (repo_path / "pkg").mkdir(parents=True)
        (repo_path / "pkg" / "__init__.py").write_text("", encoding="utf-8")
        (repo_path / "pkg" / "helpers.py").write_text(
            "def helper_value():\n    return 7\n",
            encoding="utf-8",
        )
        (repo_path / "pkg" / "service.py").write_text(
            (
                "from pkg.helpers import helper_value\n\n"
                "def use_helper():\n"
                "    return helper_value()\n"
            ),
            encoding="utf-8",
        )

        subprocess.run(
            ["git", "init"],
            cwd=repo_path,
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "CLI Test"],
            cwd=repo_path,
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            ["git", "config", "user.email", "cli-test@example.com"],
            cwd=repo_path,
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            ["git", "add", "."],
            cwd=repo_path,
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            ["git", "commit", "-m", "initial"],
            cwd=repo_path,
            check=True,
            capture_output=True,
            text=True,
        )


if __name__ == "__main__":
    unittest.main()
