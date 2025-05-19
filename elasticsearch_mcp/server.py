from elasticsearch import Elasticsearch
from mcp.server.fastmcp import FastMCP
from typing import List

from dotenv import load_dotenv
import os

# Load .env file into the environment
load_dotenv()

def createElasticsearchClient():
    # Access environment variables
    ES_URL = os.getenv('ES_URL')
    ES_API_KEY = os.getenv('ES_API_KEY')   # base64 encoded api key
    ES_USERNAME = os.getenv('ES_USERNAME')
    ES_PASSWORD = os.getenv('ES_PASSWORD')
    ES_CA_CERT = os.getenv('ES_CA_CERT')   # path to http_ca.crt file # Optional, for HTTPS verification

    if ES_API_KEY:
        return Elasticsearch(hosts=[ES_URL], api_key=ES_API_KEY, ca_certs=ES_CA_CERT)
    if ES_USERNAME and ES_PASSWORD:
        return Elasticsearch(hosts=[ES_URL], basic_auth=(ES_USERNAME, ES_PASSWORD), ca_certs=ES_CA_CERT)
    return Elasticsearch(hosts=[ES_URL])

es = createElasticsearchClient()

# Initialize FastMCP server
mcp = FastMCP("elasticsearch-mcp-server")

@mcp.tool()
def list_indices() -> List[str]:
    """
    List all available Elasticsearch indices.
        
    Returns:
        List of indices
    """
    indices = es.indices.get_alias(index="*")
    index_names = list(indices.keys())
    return index_names

@mcp.tool()
def get_mappings(index: str) -> dict:
    """
    Get field mappings for a specific Elasticsearch index.

    Args:
        index: Name of the Elasticsearch index to get mappings for

    Returns:
        Mapping schema for the specified index
    """
    mappings = es.indices.get_mapping(index=index)
    return mappings

@mcp.tool()
def search(index: str, queryBody: dict) -> dict:
    """
    Perform an Elasticsearch search with the provided query DSL. Highlights are always enabled.

    Args:
        index: Name of the Elasticsearch index to search
        queryBody: Complete Elasticsearch query DSL object that can include query, size, from, sort, etc.

    Returns:
        Search result
    """
    response = es.search(index=index, body=queryBody)
    return response

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')
