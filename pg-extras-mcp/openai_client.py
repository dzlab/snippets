from dotenv import load_dotenv
import os
from typing import List, Dict, Any, Optional
from openai import OpenAI
from openai.types.chat import ChatCompletionMessage

load_dotenv()

class OpenAIClient:
    """
    A specialized client for interacting with the OpenAI Chat Completions API,
    managing chat history internally.
    """

    def __init__(self):
        """
        Initializes the OpenAI client and an empty chat history.
        API key and base URL are loaded from environment variables.
        """
        self.client = OpenAI(api_key=os.getenv('API_KEY'), base_url=os.getenv('BASE_URL'))
        self.history: List[Dict[str, Any]] = []
        self.tools: List[Dict[str, Any]] = []

    def add_tools(self, tools: List[Dict[str, Any]]):
        """
        Args:
            tools (List[Dict[str, Any]]): A list of dictionaries defining the tools
                                           available to the AI, in OpenAI's tool format.
        """
        self.tools.extend(tools)

    def add_user_message(self, message_content: str):
        """
        Adds a user message to the chat history.

        Args:
            message_content (str): The text content of the user's message.
        """
        self.history.append({'role': 'user', 'content': message_content})

    def add_assistant_message(self, message_content: str):
        """
        Adds an assistant's text message to the chat history.

        Args:
            message_content (str): The text content of the assistant's message.
        """
        self.history.append({'role': 'assistant', 'content': message_content})

    def add_tool_calls_to_history(self, tool_calls_data: List[Dict[str, Any]]):
        """
        Adds tool calls made by the assistant to the chat history.
        The `tool_calls_data` should be in the format expected by the OpenAI API for history.

        Args:
            tool_calls_data (List[Dict[str, Any]]): A list of dictionaries, where each dictionary
                                                      represents a tool call (e.g., {'id': 'call_id', 'function': {'name': 'tool_name', 'arguments': '{"arg": "value"}'}}).
        """
        self.history.append({'role': 'assistant', 'tool_calls': tool_calls_data})

    def add_tool_response_to_history(self, tool_call_id: str, content: str):
        """
        Adds a tool's response to the chat history.

        Args:
            tool_call_id (str): The ID of the tool call that generated this response.
            content (str): The content of the tool's response, typically a JSON string.
        """
        self.history.append({
            'role': 'tool',
            'tool_call_id': tool_call_id,
            'content': content
        })

    async def get_completion(self) -> Optional[ChatCompletionMessage]:
        """
        Sends the current chat history to the OpenAI Chat Completions API
        along with available tools and retrieves the AI's response.

        Args:

        Returns:
            Optional[ChatCompletionMessage]: The message object from the AI's first choice,
                                             or None if no choices are returned.
        """
        # call LLM
        response = self.client.chat.completions.create(
            model=os.getenv("MODEL_ID", "gpt-4o-mini"),
            messages=self.history,
            tools=self.tools,
            tool_choice="auto"
        )
        if response.choices:
            return response.choices[0].message
        return None
