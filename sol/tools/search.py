import os
from typing import List, Dict, Any, Optional
from sol.tools.base import BaseTool, ToolResult
from sol.index.indexer import ASTIndexer

class SearchCodebaseTool(BaseTool):
    name = "search_codebase"
    description = "Search for function or class symbols in the codebase using Tree-sitter AST index."
    parameters = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Symbol name or substring to search for."}
        },
        "required": ["query"]
    }

    def __init__(self, indexer: ASTIndexer):
        self.indexer = indexer

    async def execute(self, query: str) -> ToolResult:
        try:
            results = self.indexer.search_symbols(query)
            if not results:
                return ToolResult(success=True, output=f"No symbols found matching '{query}'.")
            
            output_lines = [f"Found {len(results)} matching symbol(s):"]
            for r in results:
                output_lines.append(f"- [{r['kind']}] {r['name']} in {r['file_path']} (lines {r['start_line']}-{r['end_line']})")
                
            return ToolResult(success=True, output="\n".join(output_lines))
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))
