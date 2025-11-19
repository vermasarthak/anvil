import asyncio
from typing import List, Dict, Any, Callable, Awaitable
from sol.llm.base import BaseLLMProvider
from sol.llm.schema import AgentMessage
from sol.tools.base import BaseTool

class AgentLoop:
    def __init__(
        self,
        provider: BaseLLMProvider,
        tools: List[BaseTool],
        on_event_cb: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None
    ):
        self.provider = provider
        self.tools = {t.name: t for t in tools}
        self.on_event_cb = on_event_cb
        self.messages: List[AgentMessage] = []

    async def emit_event(self, event_type: str, data: Dict[str, Any]):
        if self.on_event_cb:
            await self.on_event_cb({"type": event_type, "data": data})

    async def run_task(self, prompt: str, max_steps: int = 10) -> str:
        self.messages.append(
            AgentMessage(
                role="system",
                content="You are Sol, an expert autonomous AI software engineer. Analyze the workspace, formulate a precise plan, and execute tool calls to complete the user's task."
            )
        )
        self.messages.append(AgentMessage(role="user", content=prompt))
        
        await self.emit_event("task_start", {"prompt": prompt})

        tool_schemas = [t.to_schema() for t in self.tools.values()]

        for step in range(max_steps):
            await self.emit_event("step_start", {"step": step + 1})
            
            try:
                response = await self.provider.generate(self.messages, tools=tool_schemas)
            except Exception as e:
                err_msg = f"LLM Generation Error: {str(e)}"
                await self.emit_event("error", {"error": err_msg})
                return err_msg

            if response.content:
                await self.emit_event("thinking", {"content": response.content})
                self.messages.append(AgentMessage(role="assistant", content=response.content))

            if not response.tool_calls:
                await self.emit_event("task_complete", {"result": response.content})
                return response.content or "Task completed."

            for tc in response.tool_calls:
                await self.emit_event("tool_call_start", {"name": tc.name, "arguments": tc.arguments})
                tool = self.tools.get(tc.name)
                if not tool:
                    res_text = f"Error: Tool {tc.name} not available."
                    success = False
                else:
                    t_res = await tool.execute(**tc.arguments)
                    res_text = t_res.output if t_res.success else f"Error: {t_res.error}\nOutput: {t_res.output}"
                    success = t_res.success

                await self.emit_event("tool_call_end", {"name": tc.name, "success": success, "output": res_text})
                
                self.messages.append(
                    AgentMessage(
                        role="tool",
                        content=res_text,
                        tool_call_id=tc.id,
                        name=tc.name
                    )
                )

        final_msg = "Task reached maximum execution step limit."
        await self.emit_event("task_limit_reached", {"message": final_msg})
        return final_msg
