# Elasticsearch MCP Server

This project provides an Model Context Protocol (MCP) server that allows interaction with an Elasticsearch cluster. It exposes tools to list indices, retrieve mappings, and perform searches.

Learn more about this project by reading this [blog post](https://dzlab.github.io/genai/2025/05/18/elasticsearch-mcp/).

## Features

- List available Elasticsearch indices.
- Get the mapping schema for a specific index.
- Perform searches using Elasticsearch Query DSL.

## Setup

### Prerequisites

- Python 3.11 or higher.
- `uv` installed (`pip install uv` or follow instructions at [https://docs.astral.sh/uv/](https://docs.astral.sh/uv/)).
- Access to an Elasticsearch cluster.

### Installation

Navigate to the project directory and install the dependencies:

```elasticsearch_mcp/README.md
uv sync
```

### Configuration

#### Elasticsearch Connection

Create a `.env` file in the project root directory (`elasticsearch_mcp/.env`) to configure the connection to your Elasticsearch cluster. You can use either an API key or username/password for authentication.

Using API Key:

```elasticsearch_mcp/.env
ES_URL=YOUR_ELASTICSEARCH_URL
ES_API_KEY=YOUR_BASE64_ENCODED_API_KEY
# ES_CA_CERT=/path/to/http_ca.crt # Optional, for HTTPS verification
```

Using Username/Password:

```elasticsearch_mcp/.env
ES_URL=YOUR_ELASTICSEARCH_URL
ES_USERNAME=YOUR_ELASTICSEARCH_USERNAME
ES_PASSWORD=YOUR_ELASTICSEARCH_PASSWORD
# ES_CA_CERT=/path/to/http_ca.crt # Optional, for HTTPS verification
```

Replace `YOUR_ELASTICSEARCH_URL`, `YOUR_BASE64_ENCODED_API_KEY`, `YOUR_ELASTICSEARCH_USERNAME`, and `YOUR_ELASTICSEARCH_PASSWORD` with your actual Elasticsearch cluster details. The `ES_CA_CERT` is optional and needed if you require HTTPS certificate verification.

#### MCP Client Configuration

If you are using a client like Claude Desktop that supports MCP, you will need to configure it to run this server. An example configuration for `claude_desktop_config.json` is provided in the project files.

```elasticsearch_mcp/claude_desktop_config.json
{
  "mcpServers": {
    "ElasticsearchServer": {
      "command": "/opt/homebrew/bin/uv",
      "args": [
		    "--directory",
		    "/path/to/your/elasticsearch_mcp", # Update this path
        "run",
        "server.py"
      ]
    }
  }
}
```

Update the `--directory` argument to the absolute path of your `elasticsearch_mcp` project directory.

## Running the Server

You can run the server manually from the project directory for testing, or via an MCP client:

```elasticsearch_mcp/README.md
uv run server.py
```

When run manually, the server will use `stdio` for communication. An MCP client will typically handle running the command configured in its settings.

## Available Tools

The server exposes the following tools via MCP:

-   `list_indices()`: Returns a list of all index names in the connected Elasticsearch cluster.
-   `get_mappings(index: str)`: Returns the mapping schema (structure) for the specified index.
-   `search(index: str, queryBody: dict)`: Executes an Elasticsearch search query against the specified index using the provided query body (Elasticsearch Query DSL). Highlights are always enabled.

You can interact with these tools using an MCP-compatible client. Refer to your client's documentation for how to call these tools.
