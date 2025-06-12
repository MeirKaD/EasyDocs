from fastmcp import FastMCP
from src.graph import create_demo_graph  
import asyncio

graph = create_demo_graph()
mcp = FastMCP("API-Documentation-Agent")

@mcp.tool()
async def generate_api_docs(question: str) -> str:
    """Generate API documentation from a natural language query"""
    
    initial_state = {
        "query": question,
        "platform": "",
        "action_plan": [],
        "extracted_content": "",
        "final_response": "",
        "error": None,
        "operation_type": "",
        "confidence": 0.0,
        "estimated_duration": 0,
        "complexity_level": "",
        "current_step": 0,
        "confidence_level": None,
        "explanation": None
    }
    
    try:
        result = await graph.ainvoke(initial_state)
        return result.get("final_response", "No documentation generated")
    except Exception as e:
        return f"Error generating documentation: {str(e)}"


if __name__ == "__main__":
    mcp.run(transport="stdio")