import asyncio
import json
from typing import Dict, Any
from src.graph import create_demo_graph
from src.state import DemoState

def print_separator(title: str):
    """Print a visual separator for better output readability."""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def print_state_summary(state: Dict[str, Any], node_name: str):
    """Print a summary of the current state after each node."""
    print(f"\n📊 STATE AFTER '{node_name.upper()}':")
    print("-" * 40)
    
    # Core fields that should always be present
    core_fields = ['query', 'platform', 'operation_type', 'confidence']
    for field in core_fields:
        if field in state:
            print(f"  {field}: {state[field]}")
    
    # Node-specific fields
    if 'action_plan' in state and state['action_plan']:
        print(f"  action_plan: {len(state['action_plan'])} steps")
        for i, step in enumerate(state['action_plan'][:3], 1):  # Show first 3 steps
            print(f"    {i}. {step[:60]}...")
        if len(state['action_plan']) > 3:
            print(f"    ... and {len(state['action_plan']) - 3} more steps")
    
    if 'confidence_level' in state and state['confidence_level']:
        print(f"  confidence_level: {state['confidence_level']}/10")
    
    if 'explanation' in state and state['explanation']:
        print(f"  explanation: {state['explanation'][:100]}...")
    
    if 'extracted_content' in state and state['extracted_content']:
        content_length = len(state['extracted_content'])
        print(f"  extracted_content: {content_length} characters")
        # Show first few lines
        lines = state['extracted_content'].split('\n')[:3]
        for line in lines:
            if line.strip():
                print(f"    > {line[:80]}...")
    
    if 'final_response' in state and state['final_response']:
        response_length = len(state['final_response'])
        print(f"  final_response: {response_length} characters")
        # Show first line of response
        first_line = state['final_response'].split('\n')[0]
        print(f"    > {first_line[:80]}...")
    
    if 'error' in state and state['error']:
        print(f"  ⚠️  error: {state['error']}")

async def test_graph_execution():
    """Test the complete graph execution with state flow validation."""
    
    print_separator("LANGGRAPH DEMO - FULL GRAPH TEST")
    
    # Create the compiled graph
    try:
        graph = create_demo_graph()
        print("✅ Graph compiled successfully")
    except Exception as e:
        print(f"❌ Failed to compile graph: {e}")
        return
    
    # Test queries for different scenarios
    test_queries = [
        # {
        #     "name": "Bright Data POST Request",
        #     "query": "How to send a POST request to Bright Data's Web Scraper API",
        #     "expected_platform": "bright_data"
        # },
        # {
        #     "name": "Stripe API Request", 
        #     "query": "How to create a payment intent with Stripe API",
        #     "expected_platform": "stripe"
        # },
        {
            "name": "OpenAI Chat Completion",
            "query": "How to make a chat completion request to OpenAI API",
            "expected_platform": "openai"
        }
    ]
    
    for test_case in test_queries:
        print_separator(f"TESTING: {test_case['name']}")
        
        # Initial state
        initial_state = {
            "query": test_case["query"],
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
        
        print(f"🚀 Starting execution for: '{test_case['query']}'")
        
        try:
            # Execute the graph using astream for step-by-step monitoring
            print("\n📈 EXECUTION FLOW:")
            print("-" * 40)
            
            step_count = 0
            async for event in graph.astream(initial_state):
                step_count += 1
                
                # LangGraph returns events in format: {node_name: state_update}
                for node_name, state_update in event.items():
                    print(f"\n🔄 Step {step_count}: Executing '{node_name}'")
                    
                    # Validate that state is being updated correctly
                    if not state_update:
                        print(f"⚠️  Warning: No state update from '{node_name}'")
                        continue
                    
                    # Print state summary
                    print_state_summary(state_update, node_name)
                    
                    # Validate expected behavior per node
                    validate_node_output(node_name, state_update, test_case)
            
            print_separator("EXECUTION COMPLETED")
            print(f"✅ Graph executed successfully in {step_count} steps")
            
            # Get final state for validation
            final_state = await graph.ainvoke(initial_state)
            validate_final_state(final_state, test_case)
            
        except Exception as e:
            print(f"❌ Graph execution failed: {e}")
            print(f"Error type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
        
        print("\n" + "🔚 TEST COMPLETED" + "\n")

def validate_node_output(node_name: str, state: Dict[str, Any], test_case: Dict[str, Any]):
    """Validate that each node produces expected outputs."""
    
    if node_name == "analyze_query":
        if 'platform' not in state or not state['platform']:
            print("❌ analyze_query: Missing platform identification")
        elif state['platform'] == test_case['expected_platform']:
            print(f"✅ analyze_query: Correctly identified platform as '{state['platform']}'")
        else:
            print(f"⚠️  analyze_query: Expected '{test_case['expected_platform']}', got '{state['platform']}'")
        
        if 'operation_type' not in state:
            print("❌ analyze_query: Missing operation_type")
        else:
            print(f"✅ analyze_query: Operation type identified as '{state['operation_type']}'")
    
    elif node_name == "generate_plan":
        if 'action_plan' not in state or not state['action_plan']:
            print("❌ generate_plan: No action plan generated")
        elif len(state['action_plan']) < 3:
            print(f"⚠️  generate_plan: Short action plan ({len(state['action_plan'])} steps)")
        else:
            print(f"✅ generate_plan: Generated {len(state['action_plan'])} step action plan")
        
        if 'estimated_duration' in state and state['estimated_duration'] > 0:
            print(f"✅ generate_plan: Estimated duration: {state['estimated_duration']}s")
    
    elif node_name == "execute_browser":
        if 'extracted_content' not in state or not state['extracted_content']:
            print("❌ execute_browser: No content extracted")
        else:
            content_length = len(state['extracted_content'])
            print(f"✅ execute_browser: Extracted {content_length} characters of content")
        
        if 'confidence_level' in state and state['confidence_level']:
            level = state['confidence_level']
            if level >= 8:
                print(f"✅ execute_browser: High confidence extraction ({level}/10)")
            elif level >= 6:
                print(f"⚠️  execute_browser: Medium confidence extraction ({level}/10)")
            else:
                print(f"❌ execute_browser: Low confidence extraction ({level}/10)")
    
    elif node_name == "generate_response":
        if 'final_response' not in state or not state['final_response']:
            print("❌ generate_response: No final response generated")
        else:
            response_length = len(state['final_response'])
            print(f"✅ generate_response: Generated {response_length} character response")
            
            # Check for key elements in response
            response = state['final_response'].lower()
            has_curl = 'curl' in response
            has_endpoint = 'http' in response
            has_auth = 'authorization' in response or 'bearer' in response
            
            print(f"  - Contains cURL example: {'✅' if has_curl else '❌'}")
            print(f"  - Contains endpoint URL: {'✅' if has_endpoint else '❌'}")
            print(f"  - Contains authentication: {'✅' if has_auth else '❌'}")

def validate_final_state(final_state: Dict[str, Any], test_case: Dict[str, Any]):
    """Validate the final state has all required fields."""
    
    print_separator("FINAL STATE VALIDATION")
    
    required_fields = [
        'query', 'platform', 'action_plan', 'extracted_content', 
        'final_response', 'operation_type'
    ]
    
    missing_fields = []
    empty_fields = []
    
    for field in required_fields:
        if field not in final_state:
            missing_fields.append(field)
        elif not final_state[field]:
            empty_fields.append(field)
    
    if missing_fields:
        print(f"❌ Missing fields: {missing_fields}")
    
    if empty_fields:
        print(f"⚠️  Empty fields: {empty_fields}")
    
    if not missing_fields and not empty_fields:
        print("✅ All required fields present and populated")
    
    # Check state consistency
    if final_state.get('platform') == test_case['expected_platform']:
        print(f"✅ Platform consistency maintained: '{final_state['platform']}'")
    else:
        print(f"❌ Platform inconsistency: expected '{test_case['expected_platform']}', got '{final_state.get('platform')}'")

async def test_individual_node():
    """Test individual nodes in isolation."""
    
    print_separator("INDIVIDUAL NODE TESTING")
    
    from src.nodes import analyze_query, generate_plan, execute_browser, generate_response
    
    # Test analyze_query
    test_state = {
        "query": "How to send a POST request to Stripe API for payment processing",
        "platform": "",
        "operation_type": "",
        "confidence": 0.0
    }
    
    print("🧪 Testing analyze_query node...")
    try:
        result = await analyze_query(test_state)
        print(f"✅ analyze_query result: {result}")
    except Exception as e:
        print(f"❌ analyze_query failed: {e}")

async def main():
    """Main test function."""
    
    print("🚀 STARTING LANGGRAPH DEMO TESTS")
    print("This will test the complete graph execution and state flow validation")
    
    # Test the complete graph
    await test_graph_execution()
    
    # Optional: Test individual nodes
    # await test_individual_node()
    
    print_separator("ALL TESTS COMPLETED")

if __name__ == "__main__":
    asyncio.run(main())