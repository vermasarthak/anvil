import os
from sol.tools.shell import RunCommandTool

class Verifier:
    def __init__(self, workspace_path: str = "."):
        self.workspace_path = workspace_path
        self.shell_tool = RunCommandTool()

    async def verify(self) -> dict:
        """Auto-detect test suite (pytest, npm test) and execute verification."""
        results = {"pytest": None, "npm_test": None, "passed": True, "logs": ""}
        
        # Check pytest
        if os.path.exists(os.path.join(self.workspace_path, "pytest.ini")) or os.path.exists(os.path.join(self.workspace_path, "tests")):
            res = await self.shell_tool.execute("pytest", cwd=self.workspace_path, timeout=30)
            results["pytest"] = res.success
            results["logs"] += f"\n--- Pytest Output ---\n{res.output}\n"
            if not res.success:
                results["passed"] = False
                
        # Check npm test
        pkg_json = os.path.join(self.workspace_path, "package.json")
        if os.path.exists(pkg_json):
            res = await self.shell_tool.execute("npm test", cwd=self.workspace_path, timeout=30)
            results["npm_test"] = res.success
            results["logs"] += f"\n--- NPM Test Output ---\n{res.output}\n"
            if not res.success:
                results["passed"] = False
                
        return results
