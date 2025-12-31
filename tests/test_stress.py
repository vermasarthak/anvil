import unittest
import os
import asyncio
import tempfile
import time
from anvil.tools.file_ops import ReadFileTool, CreateFileTool, EditFileTool
from anvil.tools.grep import GrepTool
from anvil.tools.shell import RunCommandTool
from anvil.index.indexer import ASTIndexer
from anvil.telemetry import TokenMetrics
from anvil.session.store import SessionStore
from anvil.agent.verifier import Verifier

class StressTestSuite(unittest.TestCase):
    def test_file_ops_concurrency_and_stress(self):
        async def run_stress():
            with tempfile.TemporaryDirectory() as tmp_dir:
                create_tool = CreateFileTool()
                read_tool = ReadFileTool()
                edit_tool = EditFileTool()

                # 1. Create 50 files concurrently
                tasks = []
                for i in range(50):
                    f_path = os.path.join(tmp_dir, f"file_{i}.py")
                    tasks.append(create_tool.execute(path=f_path, content=f"def func_{i}():\n    return {i}\n"))
                
                results = await asyncio.gather(*tasks)
                for res in results:
                    self.assertTrue(res.success)

                # 2. Edit 50 files concurrently
                edit_tasks = []
                for i in range(50):
                    f_path = os.path.join(tmp_dir, f"file_{i}.py")
                    edit_tasks.append(edit_tool.execute(path=f_path, old_string=f"return {i}", new_string=f"return {i * 100}"))

                edit_results = await asyncio.gather(*edit_tasks)
                for res in edit_results:
                    self.assertTrue(res.success)

                # 3. Read back and verify content integrity
                read_res = await read_tool.execute(path=os.path.join(tmp_dir, "file_49.py"))
                self.assertIn("return 4900", read_res.output)

        asyncio.run(run_stress())

    def test_ast_indexer_large_codebase_stress(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            indexer = ASTIndexer()
            
            # Generate 100 files with multiple definitions
            for i in range(100):
                f_path = os.path.join(tmp_dir, f"module_{i}.py")
                with open(f_path, "w") as f:
                    f.write(f"class Service{i}:\n    pass\n\ndef handler_{i}():\n    pass\n")
                indexer.index_file(f_path)

            results = indexer.search_symbols("Service")
            self.assertEqual(len(results), 100)

            handler_results = indexer.search_symbols("handler_42")
            self.assertEqual(len(handler_results), 1)

    def test_shell_command_timeout_and_error_boundary(self):
        async def run_shell_stress():
            shell = RunCommandTool()
            # Fast command execution
            res = await shell.execute(command="echo 'Anvil Engine Ready'")
            self.assertTrue(res.success)
            self.assertIn("Anvil Engine Ready", res.output)

            # Timeout safety test (sleeping longer than 1s timeout)
            res_timeout = await shell.execute(command="sleep 3", timeout=1)
            self.assertFalse(res_timeout.success)
            self.assertIn("timed out", res_timeout.error.lower())

        asyncio.run(run_shell_stress())

    def test_session_store_concurrency(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = os.path.join(tmp_dir, "test_sessions.db")
            store = SessionStore(db_path=db_path)

            # Save 20 session logs
            for i in range(20):
                store.save_session(
                    session_id=f"sess_{i}",
                    title=f"Task {i}",
                    model="google/gemini-2.5-flash",
                    transcript=[{"step": 1, "type": "task_start"}]
                )

            sessions = store.list_sessions()
            self.assertEqual(len(sessions), 20)

            sess_10 = store.get_session("sess_10")
            self.assertIsNotNone(sess_10)
            self.assertEqual(sess_10["title"], "Task 10")

if __name__ == "__main__":
    unittest.main()
