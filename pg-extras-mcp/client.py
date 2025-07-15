from dotenv import load_dotenv
import os # Import the os module to access environment variables
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from typing import List, Dict, Any, Optional
import asyncio
from openai import OpenAI # Import the OpenAI client

load_dotenv()

class ChatBot:

    def __init__(self):
        # Initialize session and client objects
        self.session: Optional[ClientSession] = None
        self.client = OpenAI(api_key=os.getenv('API_KEY'), base_url=os.getenv('BASE_URL'))
        self.available_tools: List[Dict[str, Any]] = []

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

    async def process_query(self, query):
        history = [{'role': 'user', 'content': query}]

        tools = [self._convert_mcp_to_openai_tool_format(tool) for tool in self.available_tools]

        response = self.client.chat.completions.create(
            model=os.getenv("MODEL_ID", "gpt-4o-mini"),
            messages=history,
            tools=tools,
            tool_choice="auto"
        )
        # print(response)
        process_query = True
        while process_query:
            # print("Entering process_query loop.")
            if response.choices:
                message = response.choices[0].message
                if message.content:
                        # print(f"OpenAI response content type: Text")
                        # print(message.content)
                        history.append({'role': 'assistant', 'content': message.content})
                        process_query = False
                elif message.tool_calls:
                        # print(f"OpenAI response content type: ToolCall")
                        tool_calls = message.tool_calls
                        tool_responses = []
                        for tool_call in tool_calls:
                            tool_name = tool_call.function.name
                            tool_args = json.loads(tool_call.function.arguments)

                            # print(f"Calling tool {tool_name} with args {tool_args}")

                            # tool invocation through the client session
                            result = await self.session.call_tool(tool_name, arguments=tool_args)
                            # print(f"Tool call result: {result.content}")
                            tool_responses.append({
                                'tool_call_id': tool_call.id,
                                'content': json.dumps({'results': [json.loads(textContent.text) for textContent in result.content]})
                            })

                        history.append({'role': 'assistant', 'tool_calls': tool_calls})
                        for tool_response in tool_responses:
                            history.append({'role': 'tool', **tool_response})

                        # print("Generating content after tool call...")
                        response = self.client.chat.completions.create(
                            model=os.getenv("MODEL_ID"),
                            messages=history,
                            tools=tools,
                            tool_choice="auto"
                        )

                        if response.choices and response.choices[0].message.content:
                            print(response.choices[0].message.content)
                            process_query = False
                        else:
                            print("No text part in OpenAI response after tool call or no candidates.")
                            pass # Let the loop continue to check next response type
                else:
                    print("No content parts in OpenAI response candidate.")
                    process_query = False
            else:
                print("No candidates in OpenAI response.")
                process_query = False



    async def chat_loop(self):
        """Run an interactive chat loop"""
        print("\nMCP Chatbot Started!")
        print("Type your queries or 'quit' to exit.")

        while True:
            try:
                query = input("\nQuery: ").strip()

                if query.lower() == 'quit':
                    break

                await self.process_query(query)
                print("\n")

            except Exception as e:
                print(f"\nError: {str(e)}")

    async def connect_to_server_and_run(self):
        # Create server parameters for stdio connection
        server_params = StdioServerParameters(
            command="uv",  # Executable
            args=["run", "server.py"],  # Optional command line arguments
            env=None,  # Optional environment variables
        )
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                self.session = session
                # Initialize the connection
                await session.initialize()

                # List available tools
                response = await session.list_tools()

                tools = response.tools
                print("\nConnected to server with tools:", [tool.name for tool in tools])

                self.available_tools = [{ # Storing in a consistent format
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema
                } for tool in response.tools]

                # Configure the Gemini model with available tools
                # No need to reconfigure OpenAI client with tools here, it's done per request

                await self.chat_loop()


async def main():
    chatbot = ChatBot()
    await chatbot.connect_to_server_and_run()


import json # Import json for parsing tool arguments and content

if __name__ == "__main__":
    asyncio.run(main())
