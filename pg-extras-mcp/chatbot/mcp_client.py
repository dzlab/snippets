from typing import List, Dict, Any, Optional
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import json
import asyncio

class McpClient:
    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.available_tools: List[Dict[str, Any]] = []
        self._stdio_client_context = None # To hold the stdio_client context manager
        self._client_session_context = None # To hold the ClientSession context manager

    async def __aenter__(self):
        server_params = StdioServerParameters(
            command="uv",
            args=["run", "server.py"],
            env=None,
        )
        try:
            # Manually enter stdio_client and ClientSession contexts
            self._stdio_client_context = stdio_client(server_params)
            read, write = await asyncio.wait_for(self._stdio_client_context.__aenter__(), timeout=30.0)

            self._client_session_context = ClientSession(read, write)
            self.session = await asyncio.wait_for(self._client_session_context.__aenter__(), timeout=30.0)

            await self.session.initialize()
            response = await self.session.list_tools()
            self.available_tools = [{
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.inputSchema
            } for tool in response.tools]
            print("\nConnected to server with tools:", [tool.name for tool in response.tools])
            return self # Return self for 'as' clause in async with
        except asyncio.TimeoutError:
            # Ensure cleanup if timeout happens during __aenter__
            if self.session and self._client_session_context:
                await self._client_session_context.__aexit__(None, None, None)
            if self._stdio_client_context:
                await self._stdio_client_context.__aexit__(None, None, None)
            raise Exception("Failed to connect to MCP server within the specified timeout.")

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session and self._client_session_context:
            await self._client_session_context.__aexit__(exc_type, exc_val, exc_tb)
        if self._stdio_client_context:
            await self._stdio_client_context.__aexit__(exc_type, exc_val, exc_tb)
        self.session = None # Clear session on exit

    def _clean_schema(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively removes 'title' fields from a schema dictionary."""
        cleaned_schema = {}
        for key, value in schema.items():
            if key == "title":
                continue  # Skip the title field
            if isinstance(value, dict):
                cleaned_schema[key] = self._clean_schema(value)
            elif isinstance(value, list):
                cleaned_schema[key] = [self._clean_schema(item) if isinstance(item, dict) else item for item in value]
            else:
                cleaned_schema[key] = value
        return cleaned_schema

    def _convert_mcp_to_openai_tool_format(self, mcp_tool_schema: dict) -> Dict[str, Any]:
        """Converts MCP tool schema to OpenAI tool format."""
        cleaned_input_schema = self._clean_schema(mcp_tool_schema["input_schema"])
        return {
            "type": "function",
            "function": {
                "name": mcp_tool_schema["name"],
                "description": mcp_tool_schema["description"],
                "parameters": cleaned_input_schema
            }
        }

    async def call_mcp_tool(self, tool_name: str, tool_args: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Calls an MCP tool and returns its content."""
        if not self.session:
            raise RuntimeError("McpClient session is not active. Ensure it's used within an async with statement.")
        result = await self.session.call_tool(tool_name, arguments=tool_args)
        return [json.loads(textContent.text) for textContent in result.content]

    def get_openai_tools_format(self) -> List[Dict[str, Any]]:
        """Returns the available tools in OpenAI format."""
        return [self._convert_mcp_to_openai_tool_format(tool) for tool in self.available_tools]
