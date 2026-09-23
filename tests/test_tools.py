import asyncio
import os
import tempfile
import unittest

from anvil.index.indexer import ASTIndexer
from anvil.telemetry import TokenMetrics
from anvil.tools.file_ops import CreateFileTool, EditFileTool, ReadFileTool
from anvil.tools.grep import GrepTool


class TestAnvilSuite(unittest.TestCase):
    def test_file_ops_tools(self):
        async def run_test():
            with tempfile.TemporaryDirectory() as tmp_dir:
                test_file = os.path.join(tmp_dir, "test.py")

                # Test Create
                create_tool = CreateFileTool()
                res = await create_tool.execute(path=test_file, content="def foo():\n    return 42\n")
                self.assertTrue(res.success)
                self.assertTrue(os.path.exists(test_file))

                # Test Read
                read_tool = ReadFileTool()
                res_read = await read_tool.execute(path=test_file)
                self.assertTrue(res_read.success)
                self.assertIn("return 42", res_read.output)

                # Test Edit
                edit_tool = EditFileTool()
                res_edit = await edit_tool.execute(path=test_file, old_string="return 42", new_string="return 100")
                self.assertTrue(res_edit.success)

                res_read2 = await read_tool.execute(path=test_file)
                self.assertIn("return 100", res_read2.output)

        asyncio.run(run_test())

    def test_grep_tool(self):
        async def run_test():
            with tempfile.TemporaryDirectory() as tmp_dir:
                test_file = os.path.join(tmp_dir, "sample.py")
                with open(test_file, "w") as f:
                    f.write("def calculate_sum(a, b):\n    return a + b\n")

                grep = GrepTool()
                res = await grep.execute(query="calculate_sum", path=tmp_dir)
                self.assertTrue(res.success)
                self.assertIn("sample.py", res.output)

        asyncio.run(run_test())

    def test_ast_indexer(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_file = os.path.join(tmp_dir, "model.py")
            with open(test_file, "w") as f:
                f.write("class User:\n    pass\n\ndef get_user():\n    pass\n")

            indexer = ASTIndexer()
            indexer.index_file(test_file)
            results = indexer.search_symbols("User")
            self.assertGreaterEqual(len(results), 1)
            class_results = [r for r in results if r["kind"] == "class"]
            self.assertEqual(len(class_results), 1)

    def test_telemetry_metrics(self):
        metrics = TokenMetrics()
        metrics.record_usage(1000, 500, cost_per_1m_input=3.0, cost_per_1m_output=15.0)
        data = metrics.to_dict()
        self.assertEqual(data["prompt_tokens"], 1000)
        self.assertEqual(data["completion_tokens"], 500)
        self.assertGreater(data["estimated_cost_usd"], 0.0)


if __name__ == "__main__":
    unittest.main()
