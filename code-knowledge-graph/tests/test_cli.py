import subprocess
import sys
import unittest
from pathlib import Path


class CliSmokeTest(unittest.TestCase):
    def test_module_help_works(self):
        project_root = Path(__file__).resolve().parents[1]

        result = subprocess.run(
            [sys.executable, "-m", "codekg", "--help"],
            cwd=project_root,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(0, result.returncode)
        self.assertIn("usage:", result.stdout)


if __name__ == "__main__":
    unittest.main()
