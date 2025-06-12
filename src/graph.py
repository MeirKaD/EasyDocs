from langgraph.graph import StateGraph
from .state import DemoState
from .nodes import analyze_query, generate_plan, execute_browser, generate_response

def create_demo_graph():
   workflow = StateGraph(DemoState)
   
   workflow.add_node("analyze_query", analyze_query)
   workflow.add_node("generate_plan", generate_plan) 
   workflow.add_node("execute_browser", execute_browser)
   workflow.add_node("generate_response", generate_response)
   
   workflow.add_edge("analyze_query", "generate_plan")
   workflow.add_edge("generate_plan", "execute_browser") 
   workflow.add_edge("execute_browser", "generate_response")
   
   workflow.set_entry_point("analyze_query")
   workflow.set_finish_point("generate_response")
   
   return workflow.compile()