"""
State definitions for LangGraph workflow
"""

from typing import TypedDict, Dict, Any, List, Annotated
from langgraph.graph.message import add_messages


class DocumentState(TypedDict):
    """
    State object that flows through the LangGraph workflow.
    Each agent reads from and writes to this shared state.
    """
    
    # Input information
    file_path: str
    filename: str
    
    # Document intake stage outputs
    metadata: Dict[str, Any]
    text_content: str
    text_preview: str
    preview_images: List[str]
    
    # Vision analysis stage outputs
    vision_analysis: Dict[str, Any]
    
    # Text classification stage outputs
    text_analysis: Dict[str, Any]
    
    # Domain router stage outputs
    final_decision: Dict[str, Any]
    final_domain: str
    confidence: float
    
    # File organization stage outputs
    organization_result: Dict[str, Any]
    output_path: str
    
    # Control flow and status
    processing_stage: str
    error: str
    messages: Annotated[List[str], add_messages]


class IntakeState(TypedDict):
    """State for document intake processing"""
    file_path: str
    filename: str
    file_size: int
    page_count: int
    metadata: Dict[str, Any]


class AnalysisState(TypedDict):
    """State for analysis stages (vision and text)"""
    filename: str
    text_content: str
    preview_images: List[str]
    metadata: Dict[str, Any]


class ClassificationState(TypedDict):
    """State for classification results"""
    primary_domain: str
    confidence: float
    reasoning: str
    keywords: List[str]
    alternative_domains: List[str]


class RouterState(TypedDict):
    """State for router decision"""
    filename: str
    vision_analysis: Dict[str, Any]
    text_analysis: Dict[str, Any]
    metadata: Dict[str, Any]


class OrganizationState(TypedDict):
    """State for file organization"""
    file_path: str
    filename: str
    domain: str
    operation: str


# Processing stages enum
class ProcessingStage:
    """Processing stage constants"""
    PENDING = "pending"
    INTAKE_STARTED = "intake_started"
    INTAKE_COMPLETE = "intake_complete"
    ANALYSIS_STARTED = "analysis_started"
    VISION_COMPLETE = "vision_complete"
    TEXT_COMPLETE = "text_complete"
    ROUTING_STARTED = "routing_started"
    ROUTING_COMPLETE = "routing_complete"
    ORGANIZATION_STARTED = "organization_started"
    ORGANIZATION_COMPLETE = "organization_complete"
    COMPLETED = "completed"
    FAILED = "failed"


# Agent result wrapper
class AgentResult(TypedDict):
    """Standard format for agent execution results"""
    agent_name: str
    success: bool
    result: Dict[str, Any]
    error: str
    execution_time: float
    timestamp: str


# Workflow configuration
class WorkflowConfig:
    """Configuration for workflow behavior"""
    
    # Timeouts (in seconds)
    INTAKE_TIMEOUT = 60
    VISION_TIMEOUT = 30
    TEXT_TIMEOUT = 30
    ROUTER_TIMEOUT = 20
    ORGANIZATION_TIMEOUT = 30
    
    # Retry configuration
    MAX_RETRIES = 3
    RETRY_DELAY = 5
    
    # Processing limits
    MAX_PAGES_TO_PROCESS = 100
    MAX_TEXT_LENGTH = 50000
    MAX_PREVIEW_IMAGES = 3
    
    # Confidence thresholds
    MIN_CONFIDENCE_THRESHOLD = 0.3
    HIGH_CONFIDENCE_THRESHOLD = 0.8
    
    # Agent weights for router decision
    VISION_WEIGHT = 0.3
    TEXT_WEIGHT = 0.7


# Error types
class WorkflowError:
    """Workflow error types"""
    INTAKE_ERROR = "intake_error"
    VISION_ERROR = "vision_error"
    TEXT_ERROR = "text_error"
    ROUTER_ERROR = "router_error"
    ORGANIZATION_ERROR = "organization_error"
    TIMEOUT_ERROR = "timeout_error"
    VALIDATION_ERROR = "validation_error"


def create_initial_state(file_path: str, filename: str) -> DocumentState:
    """Create initial workflow state"""
    return DocumentState(
        file_path=file_path,
        filename=filename,
        metadata={},
        text_content="",
        text_preview="",
        preview_images=[],
        vision_analysis={},
        text_analysis={},
        final_decision={},
        final_domain="general",
        confidence=0.0,
        organization_result={},
        output_path="",
        processing_stage=ProcessingStage.PENDING,
        error="",
        messages=[]
    )


def validate_state(state: DocumentState) -> tuple[bool, str]:
    """
    Validate workflow state
    
    Returns:
        (is_valid, error_message)
    """
    if not state.get("file_path"):
        return False, "Missing file_path"
    
    if not state.get("filename"):
        return False, "Missing filename"
    
    return True, ""


def merge_states(state1: DocumentState, state2: Dict[str, Any]) -> DocumentState:
    """Merge two state dictionaries"""
    merged = state1.copy()
    
    for key, value in state2.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            # Merge dictionaries
            merged[key] = {**merged[key], **value}
        elif key in merged and isinstance(merged[key], list) and isinstance(value, list):
            # Extend lists
            merged[key] = merged[key] + value
        else:
            # Replace value
            merged[key] = value
    
    return merged


def extract_agent_state(state: DocumentState, agent_name: str) -> Dict[str, Any]:
    """Extract relevant state for a specific agent"""
    if agent_name == "DocumentIntakeAgent":
        return {
            "file_path": state.get("file_path"),
            "filename": state.get("filename")
        }
    elif agent_name == "VisionAnalysisAgent":
        return {
            "preview_images": state.get("preview_images", []),
            "filename": state.get("filename"),
            "metadata": state.get("metadata", {})
        }
    elif agent_name == "TextClassificationAgent":
        return {
            "text_content": state.get("text_content", ""),
            "filename": state.get("filename"),
            "metadata": state.get("metadata", {})
        }
    elif agent_name == "DomainRouterAgent":
        return {
            "filename": state.get("filename"),
            "vision_analysis": state.get("vision_analysis", {}),
            "text_analysis": state.get("text_analysis", {}),
            "metadata": state.get("metadata", {})
        }
    elif agent_name == "FileOrganizationAgent":
        return {
            "file_path": state.get("file_path"),
            "filename": state.get("filename"),
            "domain": state.get("final_domain", "general"),
            "operation": "copy"
        }
    
    return {}