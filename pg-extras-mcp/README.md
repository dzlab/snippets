# pg-extras-mcp

## Overview

This project provides a simple interface to execute SQL queries against a PostgreSQL database using the `FastMCP` framework. It dynamically loads SQL queries from the `./queries` directory, allowing users to interact with the database through defined tools.

The queries were copied from the [ruby-pg-extras](https://github.com/pawurb/ruby-pg-extras) project.

## Features

*   **Dynamic Query Loading:** Automatically loads SQL queries from `.sql` files in the `./queries` directory.
*   **PostgreSQL Integration:** Connects to a PostgreSQL database using environment variables for configuration.
*   **FastMCP Framework:** Utilizes the `FastMCP` framework to expose SQL queries as tools.
*   **Query Descriptions:** Extracts descriptions from the SQL files for better tool documentation.

## Prerequisites

*   Python 3.x
*   `psycopg2` (PostgreSQL adapter for Python)
*   `python-dotenv` (for loading environment variables)
*   `fastmcp`

## Installation

1.  **Clone the repository:**

    ```bash
    git clone <repository_url>
    cd pg-extras-mcp
    ```

2.  **Install dependencies:**

    ```bash
    uv sync
    ```
    *Note: you can also install the dependencies manually.*
    ```bash
    pip install psycopg2 python-dotenv fastmcp
    ```

3.  **Configure PostgreSQL connection:**

    Set the following environment variables:

    *   `PG_HOST`: PostgreSQL host (default: `localhost`)
    *   `PG_DATABASE`: PostgreSQL database name
    *   `PG_USER`: PostgreSQL user
    *   `PG_PASSWORD`: PostgreSQL password
    *   `PG_PORT`: PostgreSQL port (default: `5432`)

    You can set these variables in a `.env` file in the project root.  Example:

    ```
    PG_DATABASE=your_database_name
    PG_USER=your_username
    PG_PASSWORD=your_password
    ```

## Usage

1.  **Place SQL files in the `./queries` directory.** Each `.sql` file should contain a SQL query and can include a description at the beginning using the `--` comment syntax.
2.  **Run the server:**

    ```bash
    python server.py
    ```

    This will start the FastMCP server, making the SQL queries available as tools.

3.  **Interact with the tools**
    You can use the tools exposed by FastMCP to execute the SQL queries.

## Project Structure

```
pg-extras-mcp/
├── server.py          # Main application file.
├── queries/           # Directory containing SQL query files.
│   └── example.sql    # Example SQL query file.
├── .env               # Environment variables file (optional).
├── README.md          # This file.
└── ...
```

## Example SQL Query (`queries/example.sql`)

```sql
-- Get all users
-- Retrieves all users from the users table.
SELECT * FROM users;
```

## Contributing

Contributions are welcome!  Feel free to submit pull requests or open issues.

## License

Apache 2.0
