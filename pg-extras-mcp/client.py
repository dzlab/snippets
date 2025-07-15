from dotenv import load_dotenv
import os # Import the os module to access environment variables
from typing import List, Dict, Any, Optional
import asyncio
from mcp_client import McpClient # Import the new McpClient class
from openai_client import OpenAIClient
import json # Import json for parsing tool arguments and content

load_dotenv()

class ChatBot:

    def __init__(self):
        # Initialize client objects
        self.openai_client = OpenAIClient()
        self.mcp_client: Optional[McpClient] = None # Will be initialized in connect_to_server_and_run

    async def process_query(self, query):
        if not self.mcp_client:
            raise RuntimeError("McpClient is not initialized.")
        tools = self.mcp_client.get_openai_tools_format()

        self.openai_client.add_tools(tools)
        # append user query to history
        self.openai_client.add_user_message(query)
        message = await self.openai_client.get_completion()

        process_query = True
        while process_query:
            if message: # Check if message is not None
                if message.content:
                        self.openai_client.add_assistant_message(message.content)
                        print("\nAssistant:", message.content) # Print the content from the assistant's message
                        process_query = False
                elif message.tool_calls:
                        tool_calls = message.tool_calls
                        tool_responses = []
                        for tool_call in tool_calls:
                            tool_name = tool_call.function.name
                            tool_args = json.loads(tool_call.function.arguments)

                            if not self.mcp_client:
                                raise RuntimeError("McpClient is not initialized or connected.")

                            # tool invocation through the client session
                            result_content = await self.mcp_client.call_mcp_tool(tool_name, tool_args)
                            tool_responses.append({
                                'tool_call_id': tool_call.id,
                                'content': json.dumps({'results': result_content})
                            })

                        self.openai_client.add_tool_calls_to_history(tool_calls)
                        for tool_response in tool_responses:
                            self.openai_client.add_tool_response_to_history(
                                tool_response['tool_call_id'], tool_response['content']
                            )

                        message = await self.openai_client.get_completion()

                        if message and message.content:
                            print(message.content)
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
        self.mcp_client = McpClient()
        async with self.mcp_client as mcp_client_instance:
            # The mcp_client_instance is the fully initialized McpClient object
            # self.mcp_client is already set in __aenter__ but we can keep this for clarity
            self.mcp_client = mcp_client_instance
            await self.chat_loop()


async def main():
    chatbot = ChatBot()
    await chatbot.connect_to_server_and_run()


if __name__ == "__main__":
    asyncio.run(main())
