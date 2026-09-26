from mcp.server.fastmcp import FastMCP
from rag_pipeline import answer_question as answer_impl
from rag_pipeline import refresh_corpus as refresh_impl
from rag_pipeline import retrieve_context as retrieve_impl

mcp = FastMCP("TripAgent Shared RAG MCP")
AVAILABLE_TOOLS = ["refresh_corpus", "retrieve_context", "answer_question"]

@mcp.tool()
def refresh_corpus(feature: str, caller: str = "student"):
    return refresh_impl(feature, caller)

@mcp.tool()
def retrieve_context(query: str, feature: str, k: int = 5, caller: str = "student"):
    return retrieve_impl(query, feature, k, caller)

@mcp.tool()
def answer_question(query: str, feature: str, k: int = 5, caller: str = "student"):
    return answer_impl(query, feature, k, caller)

if __name__ == "__main__":
    print("Starting TripAgent Shared RAG MCP Server...")
    for tool in AVAILABLE_TOOLS:
        print(f"- {tool}")
    mcp.run()
