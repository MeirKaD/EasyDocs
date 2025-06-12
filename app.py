import streamlit as st
import asyncio
import json
from typing import Dict, Any
import time

from src.graph import create_demo_graph
from src.state import DemoState

STEP_DESCRIPTIONS = {
    "analyze_query": "Analyzing query and identifying platform...",
    "generate_plan": "Creating action plan for documentation extraction...",
    "execute_browser": "Executing browser automation to extract API docs...",
    "generate_response": "Generating developer-friendly documentation..."
}

async def run_agent(query: str):
    """Run your actual LangGraph agent and yield step-by-step updates."""
    
    try:
        # Create the graph
        graph = create_demo_graph()
        
        # Initial state - matching your DemoState exactly
        initial_state = {
            "query": query,
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
        
        accumulated_state = initial_state.copy()
        
        async for event in graph.astream(initial_state):
            for node_name, state_update in event.items():
                
                accumulated_state.update(state_update)
                
                yield {
                    "step": node_name,
                    "description": STEP_DESCRIPTIONS.get(node_name, f"Executing {node_name}..."),
                    "status": "running",
                    "current_state": accumulated_state.copy()
                }
                
                await asyncio.sleep(0.5)
                
                yield {
                    "step": node_name,
                    "description": STEP_DESCRIPTIONS.get(node_name, f"Completed {node_name}"),
                    "status": "completed",
                    "current_state": accumulated_state.copy(),
                    "step_results": state_update
                }
        
        yield {
            "step": "final",
            "description": "Documentation generation completed!",
            "status": "completed",
            "current_state": accumulated_state,
            "final_results": accumulated_state
        }
        
    except Exception as e:
        yield {
            "step": "error",
            "description": f"Error occurred: {str(e)}",
            "status": "error",
            "error": str(e)
        }

def main():
    st.set_page_config(
        page_title="API Documentation Agent",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    st.markdown("""
    <style>
    .main > div {
        padding-top: 2rem;
    }
    
    .stAlert {
        margin-top: 1rem;
    }
    
    .step-container {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 4px solid #4f46e5;
    }
    
    .step-running {
        border-left-color: #f59e0b;
        background: #fffbeb;
    }
    
    .step-completed {
        border-left-color: #10b981;
        background: #f0fdf4;
    }
    
    .confidence-high {
        color: #10b981;
        font-weight: bold;
    }
    
    .confidence-medium {
        color: #f59e0b;
        font-weight: bold;
    }
    
    .confidence-low {
        color: #ef4444;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

    st.title("🤖 API Documentation Agent")
    st.markdown("Generate developer-friendly API documentation from natural language queries")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.header("📝 Input")
        
        query = st.text_area(
            "Enter your API documentation query:",
            placeholder="Example: How to send a POST request to OpenAI's chat completion API",
            height=200,
            help="Describe what API documentation you need. Be specific about the platform and operation type."
        )
        
        with st.expander("💡 Example Queries"):
            st.markdown("""
            - "How to create a payment intent with Stripe API"
            - "How to send a POST request to Bright Data's Web Scraper API"
            - "How to make a chat completion request to OpenAI API"
            - "How to authenticate with Twilio API and send SMS"
            """)
        
        if st.button("🚀 Generate Documentation", type="primary", use_container_width=True):
            if query.strip():
                st.session_state.query = query
                st.session_state.processing = True
                st.rerun()
            else:
                st.error("Please enter a query first!")

    with col2:
        st.header("📊 Results")
        
        if hasattr(st.session_state, 'processing') and st.session_state.processing:
            if hasattr(st.session_state, 'query'):
                
                progress_container = st.container()
                results_container = st.container()
                
                with progress_container:
                    st.subheader("🔄 Processing Steps")
                    progress_placeholder = st.empty()
                
                async def process_query():
                    step_statuses = {}
                    final_state = None
                    error_occurred = False
                    
                    async for update in run_agent(st.session_state.query):
                        step_name = update.get("step")
                        description = update.get("description", "")
                        status = update.get("status", "running")
                        current_state = update.get("current_state", {})
                        step_results = update.get("step_results", {})
                        
                        if status == "error":
                            error_occurred = True
                            st.error(f"Error: {update.get('error', 'Unknown error occurred')}")
                            return None
                        
                        step_statuses[step_name] = {
                            "description": description,
                            "status": status
                        }
                        
                        if step_name == "final" or (status == "completed" and current_state):
                            final_state = current_state
                        
                        if step_name == "final":
                            continue
                            
                        progress_html = ""
                        for step, info in step_statuses.items():
                            if step == "final": 
                                continue
                                
                            status_class = f"step-{info['status']}"
                            if info['status'] == "running":
                                status_icon = "🟡"
                            elif info['status'] == "completed":
                                status_icon = "✅"
                            else:
                                status_icon = "❌"
                                
                            progress_html += f"""
                            <div class="step-container {status_class}">
                                <strong>{status_icon} {step.replace('_', ' ').title()}</strong><br>
                                <small>{info['description']}</small>
                            </div>
                            """
                        
                        progress_placeholder.markdown(progress_html, unsafe_allow_html=True)
                        
                        if status == "running":
                            await asyncio.sleep(0.5)
                    
                    return final_state

                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    final_state = loop.run_until_complete(process_query())
                    loop.close()
                    
                    with results_container:
                        st.subheader("📋 Generated Documentation")
                        
                        if final_state :
                            confidence = final_state.get("confidence_level")
                            if confidence is not None:
                                if confidence >= 8:
                                    st.markdown('<div class="confidence-high">🟢 High Confidence Documentation</div>', unsafe_allow_html=True)
                                elif confidence >= 6:
                                    st.markdown('<div class="confidence-medium">🟡 Medium Confidence Documentation</div>', unsafe_allow_html=True)
                                else:
                                    st.markdown('<div class="confidence-low">🔴 Low Confidence Documentation</div>', unsafe_allow_html=True)
                            
                            final_response = final_state.get("final_response", "")
                            if final_response and final_response.strip():
                                st.markdown(final_response)
                                
                                st.download_button(
                                    label="📥 Download Documentation",
                                    data=final_response,
                                    file_name=f"api_docs_{final_state.get('platform', 'generated')}.md",
                                    mime="text/markdown"
                                )
                                
                                with st.expander("🔍 Debug Information"):
                                    st.json({
                                        "platform": final_state.get("platform", "unknown"),
                                        "operation_type": final_state.get("operation_type", "unknown"),
                                        "confidence": final_state.get("confidence", 0),
                                        "confidence_level": final_state.get("confidence_level"),
                                        "estimated_duration": final_state.get("estimated_duration", 0),
                                        "complexity_level": final_state.get("complexity_level", "unknown"),
                                        "action_plan_steps": len(final_state.get("action_plan", [])),
                                        "extracted_content_length": len(final_state.get("extracted_content", "")),
                                        "explanation": final_state.get("explanation", "No explanation available")[:200] + "..." if final_state.get("explanation") and len(final_state.get("explanation", "")) > 200 else final_state.get("explanation", "No explanation available")
                                    })
                                
                            else:
                                st.error("No documentation was generated. The final_response field is empty.")
                                st.json({"final_state": final_state})
                        else:
                            st.error("Failed to generate documentation. Please check the logs and try again.")
                            if final_state:
                                st.json({"received_state": final_state})
                
                except Exception as e:
                    st.error(f"An error occurred while processing: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())
                
                finally:
                    st.session_state.processing = False
        
        else:
            st.info("👆 Enter a query and click 'Generate Documentation' to get started!")
            
            st.subheader("🎯 What This Agent Does")
            st.markdown("""
            - **Analyzes** your query to identify the API platform and operation type
            - **Plans** browser automation steps to extract documentation
            - **Executes** web scraping to gather API information
            - **Generates** clean, copy-paste ready documentation with examples
            """)

if __name__ == "__main__":
    main()