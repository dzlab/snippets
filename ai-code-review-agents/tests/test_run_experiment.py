import unittest

import run_experiment


class OpenAIErrorMessageTest(unittest.TestCase):
    def test_credit_balance_exhausted_gets_actionable_message(self):
        error = Exception("credit_balance_exhausted: You have no credits remaining.")

        message = run_experiment.describe_openai_error(error)

        self.assertIn("no credits remaining", message)
        self.assertIn("billing", message)


if __name__ == "__main__":
    unittest.main()
