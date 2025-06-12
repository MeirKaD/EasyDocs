from typing import Optional
from pydantic import BaseModel, Field
from typing import List
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from mcp_use.client import MCPClient
from mcp_use.adapters.langchain_adapter import LangChainAdapter
from langgraph.prebuilt import create_react_agent
from .state import DemoState
import os
from dotenv import load_dotenv

load_dotenv()

class QueryAnalysis(BaseModel):
    """Analysis of user query to extract platform and operation type."""
    platform: str = Field(
        description="The platform/service mentioned in the query (e.g., 'bright_data', 'stripe', 'openai', 'unknown')"
    )
    operation_type: str = Field(
        description="The type of API operation requested (e.g., 'GET', 'POST', 'authentication', 'general')"
    )
    confidence: Optional[float] = Field(
        default=None,
        description="Confidence score from 0.0 to 1.0 for the analysis"
    )

    
class BrowserExecutionResult(BaseModel):
    """Structured result from browser execution with confidence and explanation."""
    confidence_level: int = Field(
        description="Confidence level from 1-10 indicating quality of extracted documentation",
        ge=1,
        le=10
    )
    explanation: str = Field(
        description="Step-by-step explanation of what was extracted and how"
    )
    extracted_content: str = Field(
        description="The actual API documentation content that was extracted"
    )

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)
structured_llm = llm.with_structured_output(QueryAnalysis)
browser_result_llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)
structured_browser_llm = browser_result_llm.with_structured_output(BrowserExecutionResult)

async def analyze_query(state: DemoState) -> DemoState:
    query = state["query"]
    
    analysis_prompt = f"""
    Analyze the following user query to extract:
    1. The platform/service they're asking about
    2. The type of API operation they want to perform
    3. Your confidence in this analysis
    
    User Query: {query}
    
    Look for keywords like:
    - Platforms: Bright Data, Stripe, OpenAI, Twilio, etc.
    - Operations: GET request, POST request, authentication, webhook, etc.
    
    If unclear, mark platform as 'unknown' and operation as 'general'.
    """
    
    try:
        analysis = await structured_llm.ainvoke(analysis_prompt)
        
        return {
            "platform": analysis.platform.lower().replace(" ", "_"),
            "operation_type": analysis.operation_type,
            "confidence": analysis.confidence or 0.8
        }
    except Exception as e:
        query_lower = query.lower()
        if "bright data" in query_lower:
            platform = "bright_data"
        elif "stripe" in query_lower:
            platform = "stripe"
        elif "openai" in query_lower:
            platform = "openai"
        else:
            platform = "unknown"
            
        return {
            "platform": platform,
            "operation_type": "general",
            "confidence": 0.0,
            "error": f"LLM analysis failed: {str(e)}"
        }
    

class ActionPlan(BaseModel):
    """Step-by-step action plan for browser automation to extract API documentation."""
    steps: List[str] = Field(
        description="Ordered list of browser actions to extract documentation. Should be specific, actionable steps."
    )
    estimated_duration: int = Field(
        description="Estimated time in seconds to complete all steps",
        default=60
    )
    complexity_level: str = Field(
        description="Complexity level: 'simple', 'medium', or 'complex'",
        default="medium"
    )

planning_llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)
structured_planning_llm = planning_llm.with_structured_output(ActionPlan)

async def generate_plan(state: DemoState) -> DemoState:
    query = state["query"]
    platform = state["platform"]
    operation_type = state.get("operation_type", "general")
    
    planning_prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """You are an expert at creating browser automation plans to extract API documentation.
            
            Generate a step-by-step plan for browser actions that will help extract relevant API documentation.
            Each step should be specific and actionable for browser automation (navigate, search, click, extract).
            
            Focus on finding:
            - API endpoints and URLs
            - Request methods (GET, POST, etc.)
            - Required parameters and headers
            - Authentication requirements
            - Code examples or CURL commands
            
            Make steps specific to the platform and operation type requested."""
        ),
        (
            "user",
            """Create a browser automation plan for this request:
            
            Query: {query}
            Platform: {platform}
            Operation Type: {operation_type}
            
            The plan should help find specific API documentation to answer the user's query.
            Include steps to navigate to docs, search for relevant sections, and extract key information."""
        )
    ])
    
    try:
        planning_chain = planning_prompt | structured_planning_llm
        plan_response = await planning_chain.ainvoke({
            "query": query,
            "platform": platform,
            "operation_type": operation_type
        })
        
        return {
            "action_plan": plan_response.steps,
            "estimated_duration": plan_response.estimated_duration,
            "complexity_level": plan_response.complexity_level
        }
        
    except Exception as e:
        fallback_plans = {
            "bright_data": [
                "Navigate to https://docs.brightdata.com/",
                "Search for 'Web Scraper API' in documentation",
                "Locate API reference or endpoint documentation",
                "Find GET request examples and parameters",
                "Extract authentication requirements",
                "Copy relevant code examples and endpoint URLs"
            ],
            "stripe": [
                "Navigate to https://stripe.com/docs/api",
                "Search for the specific API operation requested",
                "Find endpoint documentation and examples",
                "Extract required parameters and authentication",
                "Copy CURL examples or code snippets"
            ],
            "openai": [
                "Navigate to https://platform.openai.com/docs/api-reference",
                "Search for the requested API endpoint",
                "Find endpoint documentation and parameters",
                "Extract authentication and usage examples",
                "Copy relevant request/response examples"
            ],
            "unknown": [
                "Search for '{platform} API documentation' in search engine",
                "Navigate to official documentation site",
                "Search for relevant API endpoints",
                "Extract endpoint URLs and parameters",
                "Find authentication and example requests"
            ]
        }
        
        default_plan = fallback_plans.get(platform, fallback_plans["unknown"])
        
        return {
            "action_plan": default_plan,
            "current_step": 0,
            "estimated_duration": 90,
            "complexity_level": "medium",
            "error": f"LLM planning failed, using fallback: {str(e)}"
        }

async def execute_browser(state: DemoState) -> DemoState:
    action_plan = state["action_plan"]
    query = state["query"]
    platform = state["platform"]
    
    try:
        browserai_config = {
            "mcpServers": {
                "BrightData": {
                    "command": "npx",
                    "args": ["@brightdata/mcp"],
                    "env": {
                        "API_TOKEN": os.getenv("BRIGHT_DATA_API_TOKEN"),
                        "WEB_UNLOCKER_ZONE": os.getenv("WEB_UNLOCKER_ZONE", "unblocker"),
                        "BROWSER_ZONE": os.getenv("BROWSER_ZONE", "scraping_browser")
                    }
                }
            }
        }
        
        client = MCPClient.from_dict(browserai_config)
        adapter = LangChainAdapter()
        tools = await adapter.create_tools(client)
        agent = create_react_agent(
            model=planning_llm,
            tools=tools,
            prompt = """
            You are a web search agent with comprehensive scraping capabilities. Your tools include:

            search_engine: Get search results from Google/Bing/Yandex
            scrape_as_markdown/html: Extract content from any webpage with bot detection bypass
            Structured extractors: Fast, reliable data from major platforms (Amazon, LinkedIn, Instagram, Facebook, X, TikTok, YouTube, Reddit, Zillow, etc.)
            Browser automation: Navigate, click, type, screenshot for complex interactions

            Use structured web_data_* tools for supported platforms when possible (faster/more reliable). Use general scraping for other sites. Handle errors gracefully and respect rate limits.
            """
        )
            
        result = await agent.ainvoke({
            "messages": [{
                "role": "user",
                "content": f"Query: {query}\nPlatform: {platform}\nAction Plan: {' -> '.join(action_plan)}\n\nExtract API documentation following this plan."
            }]
        })
        
        raw_content = result["messages"][-1].content
        structure_prompt = f"""
        Analyze the following extracted API documentation and provide:
        1. Confidence level (1-10) - how complete and accurate is this documentation
        2. Step-by-step explanation of what was found and extracted
        3. The extracted content itself
        
        Raw extracted content: {raw_content}
        Original query: {query}
        Platform: {platform}
        
        Rate confidence based on:
        - Completeness of API information found
        - Accuracy and relevance to the query
        - Quality of examples and documentation
        """
        
        structured_result = await structured_browser_llm.ainvoke(structure_prompt)
        
        return {
            "confidence_level": structured_result.confidence_level,
            "explanation": structured_result.explanation,
            "extracted_content": structured_result.extracted_content
        }

            
    except Exception as e:
        fallback_content = f"""
        API Documentation (Fallback for {platform})
        Query: {query}
        Platform: {platform}
        Basic API structure to look for:
        - Endpoint URLs and HTTP methods
        - Authentication requirements
        - Request parameters
        - Response examples
        """
        return {
            "extracted_content": fallback_content,
            "error": f"Browser execution failed: {str(e)}"
        }
    
response_llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro-preview-06-05", temperature=0)

async def generate_response(state: DemoState) -> DemoState:
    """Generate a developer-friendly response with copy-paste ready code."""
    
    query = state["query"]
    platform = state["platform"]
    operation_type = state.get("operation_type", "general")
    extracted_content = state.get("extracted_content", "")
    confidence_level = state.get("confidence_level", 0)
    explanation = state.get("explanation", "")
    
    response_prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """You are a technical documentation expert who creates clear, copy-paste ready API documentation for developers.

            Format your response with:
            1. Clear section headers using ##
            2. Copy-paste ready code blocks with proper syntax highlighting
            3. Step-by-step instructions
            4. Replace placeholder values with clear ALL_CAPS descriptions
            5. Include practical examples and common pitfalls
            6. Use bullet points for lists of requirements or steps
            7. Add helpful tips and notes where relevant

            Focus on making it immediately actionable for developers."""
        ),
        (
            "user",
            """Create developer-friendly documentation based on this extracted API information:

            **Original Query**: {query}
            **Platform**: {platform}
            **Operation Type**: {operation_type}
            **Confidence Level**: {confidence_level}/10
            **Extraction Process**: {explanation}

            **Extracted API Documentation**:
            {extracted_content}

            Transform this into a clean, copy-paste ready format that developers can immediately use.
            Include:
            - Clear endpoint URL
            - Required headers with placeholder explanations
            - Request body examples
            - cURL command that works out of the box (with placeholders)
            - Authentication setup
            - Common parameters
            - Quick start steps"""
        )
    ])
    
    try:
        formatting_chain = response_prompt | response_llm
        formatted_response = await formatting_chain.ainvoke({
            "query": query,
            "platform": platform,
            "operation_type": operation_type,
            "confidence_level": confidence_level,
            "explanation": explanation,
            "extracted_content": extracted_content
        })
        
        final_response = formatted_response.content
        
        confidence_indicator = "🟢 High Confidence" if confidence_level >= 8 else "🟡 Medium Confidence" if confidence_level >= 6 else "🔴 Low Confidence"
        
        final_response = f"**Documentation Quality**: {confidence_indicator} ({confidence_level}/10)\n\n{final_response}"
        
        return {
            "final_response": final_response
        }
        
    except Exception as e:
        
        return {
            "final_response": "failed generating",
            "error": f"Response generation failed, using fallback: {str(e)}"
        }
