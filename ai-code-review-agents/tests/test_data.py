import unittest

from src import data


class FixtureLoadingTest(unittest.TestCase):
    def test_repository_is_loaded_from_fixture_files(self):
        users_file = data.REPOSITORY_FIXTURE_ROOT / "app/api/users.py"

        repository = data.load_repository()

        self.assertTrue(users_file.is_file())
        self.assertEqual(11, len(repository))
        self.assertEqual(
            users_file.read_text(encoding="utf-8"),
            repository["app/api/users.py"],
        )

    def test_pull_requests_load_diffs_from_files(self):
        diff_file = data.PR_DIFF_ROOT / "pr_001_auth_bypass.diff"

        pull_requests = data.load_sample_prs()

        self.assertTrue(diff_file.is_file())
        self.assertEqual(15, len(pull_requests))
        self.assertEqual(
            diff_file.read_text(encoding="utf-8"),
            pull_requests[0]["diff"],
        )
        self.assertNotIn("diff_file", pull_requests[0])

    def test_pr_diff_helper_loads_a_diff_file(self):
        diff_file = data.PR_DIFF_ROOT / "pr_001_auth_bypass.diff"

        diff = data.load_pr_diff("pr_001_auth_bypass.diff")

        self.assertEqual(diff_file.read_text(encoding="utf-8"), diff)


if __name__ == "__main__":
    unittest.main()
