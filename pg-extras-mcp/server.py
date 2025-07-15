from mcp.server.fastmcp import FastMCP
import psycopg2
from typing import List

from dotenv import load_dotenv
import os
from functools import partial

# Load .env file into the environment
load_dotenv()

def createPostgresClient():
    PG_HOST = os.getenv('PG_HOST', 'localhost')
    PG_DATABASE = os.getenv('PG_DATABASE')
    PG_USER = os.getenv('PG_USER')
    PG_PASSWORD = os.getenv('PG_PASSWORD')
    PG_PORT = os.getenv('PG_PORT', '5432')

    try:
        conn = psycopg2.connect(
            host=PG_HOST,
            database=PG_DATABASE,
            user=PG_USER,
            password=PG_PASSWORD,
            port=PG_PORT
        )
        return conn
    except Exception as e:
        print(f"Error connecting to PostgreSQL: {e}")
        return None

pg = createPostgresClient()

def execute_sql_query(query: str) -> List[dict]:
    """
    Execute a raw SQL query against the PostgreSQL database.

    Args:
        query: The SQL query string to execute.

    Returns:
        A list of dictionaries, where each dictionary represents a row
        and keys are column names. Returns an empty list if no results
        or an error occurs.
    """
    if not pg:
        print("PostgreSQL client is not initialized.")
        return []

    results = []
    try:
        cur = pg.cursor()
        cur.execute(query)
        # Fetch column names
        column_names = [desc[0] for desc in cur.description]
        # Fetch all rows and convert to list of dictionaries
        results = [dict(zip(column_names, row)) for row in cur.fetchall()]
        cur.close()
        pg.commit() # Commit changes if any, e.g., for INSERT/UPDATE/DELETE
    except Exception as e:
        print(f"Error executing SQL query: {e}")
        if pg:
            pg.rollback() # Rollback in case of error

    return results

def list_queries() -> List[dict]:
    """
    Returns information about all SQL queries under the 'queries' folder.

    Each query's information includes its filename, description (from initial comments),
    and the SQL query content itself.
    """
    queries_dir = "./queries"
    query_info_list = []

    if not os.path.exists(queries_dir):
        print(f"Queries directory not found: {queries_dir}")
        return []

    for filename in os.listdir(queries_dir):
        if filename.endswith(".sql"):
            file_path = os.path.join(queries_dir, filename)
            description_lines = []
            sql_query_lines = []
            is_description_block = True

            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    stripped_line = line.strip()
                    if is_description_block:
                        if stripped_line.startswith('--'):
                            description_lines.append(stripped_line[2:].strip())
                        elif stripped_line == '':
                            description_lines.append('')
                        else:
                            is_description_block = False
                            sql_query_lines.append(line)
                    else:
                        sql_query_lines.append(line)

            # Remove trailing empty strings from description if any
            while description_lines and description_lines[-1] == '':
                description_lines.pop()

            description = "\n".join(description_lines).strip()
            query_content = "".join(sql_query_lines).strip()

            query_info_list.append({
                "name": os.path.splitext(filename)[0],
                "description": description,
                "body": query_content
            })
    return query_info_list

def register_tools(mcp):
    for query in list_queries():
        fct = partial(execute_sql_query, query['body'])
        fct.__name__ = query['name']
        fct.__doc__ = query['description']
        mcp.tool()(fct)

# Initialize FastMCP server
mcp = FastMCP("pg-extras-mcp")
register_tools(mcp)

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')
