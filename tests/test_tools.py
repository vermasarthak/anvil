import unittest
import os
import asyncio
import tempfile
from sol.tools.file_ops import ReadFileTool, CreateFileTool, EditFileTool

class TestFileOpsTools(unittest.TestCase):
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

if __name__ == "__main__":
    unittest.main()
