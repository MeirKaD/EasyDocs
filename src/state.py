from typing import TypedDict, List, Optional

class DemoState(TypedDict):
    query: str
    platform: str
    action_plan: List[str]
    extracted_content: str
    final_response: str
    error: Optional[str]
    operation_type: str
    confidence: float
    estimated_duration: int
    complexity_level: str
    current_step: int
    confidence_level: Optional[int]  
    explanation: Optional[str]   