import io
import sys
import unittest
from unittest.mock import patch

import run_experiment


class OpenAIErrorMessageTest(unittest.TestCase):
    def test_credit_balance_exhausted_gets_actionable_message(self):
        error = Exception("credit_balance_exhausted: You have no credits remaining.")

        message = run_experiment.describe_openai_error(error)

        self.assertIn("no credits remaining", message)
        self.assertIn("billing", message)


class DryRunOutputTest(unittest.TestCase):
    def test_dry_run_prints_selected_models(self):
        stdout = io.StringIO()
        argv = [
            "run_experiment.py",
            "--dry-run",
            "--model",
            "gpt-4o-mini",
            "--embedding-model",
            "text-embedding-3-large",
        ]

        with patch.object(sys, "argv", argv), patch("sys.stdout", stdout):
            run_experiment.main()

        output = stdout.getvalue()
        self.assertIn("model=gpt-4o-mini", output)
        self.assertIn("embedding_model=text-embedding-3-large", output)


if __name__ == "__main__":
    unittest.main()
