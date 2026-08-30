import unittest


class ImportSmokeTest(unittest.TestCase):
    def test_package_exports_model_symbols(self):
        import codekg

        self.assertTrue(hasattr(codekg, "__version__"))
        self.assertTrue(hasattr(codekg, "Node"))
        self.assertTrue(hasattr(codekg, "Edge"))
        self.assertTrue(hasattr(codekg, "ParsedGraph"))
        self.assertTrue(hasattr(codekg, "Task"))
        self.assertTrue(hasattr(codekg, "RankResult"))


if __name__ == "__main__":
    unittest.main()
