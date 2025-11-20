"""
LangGraph Workflow for Document Classification
Orchestrates multiple agents in a coordinated workflow
"""

from typing import Dict, Any, TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from loguru import logger

from agents.document_intake import DocumentIntakeAgent
from agents.vision_analysis import VisionAnalysisAgent
from agents.text_classification import TextClassificationAgent
from agents.domain_router import DomainRouterAgent
from agents.file_organization import FileOrganizationAgent


class DocumentState(TypedDict):
    """State object that flows through the graph"""
    # Input
    file_path: str
    filename: str
    
    # Intake stage
    metadata: Dict[str, Any]
    text_content: str
    text_preview: str
    preview_images: list
    
    # Analysis stages
    vision_analysis: Dict[str, Any]
    text_analysis: Dict[str, Any]
    
    # Decision stage
    final_decision: Dict[str, Any]
    final_domain: str
    confidence: float
    
    # Organization stage
    organization_result: Dict[str, Any]
    output_path: str
    
    # Control flow
    processing_stage: str
    error: str
    messages: Annotated[list, add_messages]


class DocumentClassificationWorkflow:
    """LangGraph workflow for document classification"""
    
    def __init__(self):
        # Initialize all agents
        self.intake_agent = DocumentIntakeAgent()
        self.vision_agent = VisionAnalysisAgent()
        self.text_agent = TextClassificationAgent()
        self.router_agent = DomainRouterAgent()
        self.org_agent = FileOrganizationAgent()
        
        # Build graph
        self.graph = self._build_graph()
        self.app = self.graph.compile()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow"""
        
        # Create workflow graph
        workflow = StateGraph(DocumentState)
        
        # Add nodes for each agent
        workflow.add_node("intake", self._intake_node)
        workflow.add_node("vision_analysis", self._vision_node)
        workflow.add_node("text_classification", self._text_node)
        workflow.add_node("domain_router", self._router_node)
        workflow.add_node("file_organization", self._organization_node)
        workflow.add_node("error_handler", self._error_node)
        
        # Define edges (workflow flow)
        workflow.set_entry_point("intake")
        
        workflow.add_edge("intake", "vision_analysis")
        workflow.add_edge("intake", "text_classification")
        
        # Both vision and text analysis flow to router
        workflow.add_edge("vision_analysis", "domain_router")
        workflow.add_edge("text_classification", "domain_router")
        
        workflow.add_edge("domain_router", "file_organization")
        workflow.add_edge("file_organization", END)
        
        # Error handling
        workflow.add_conditional_edges(
            "intake",
            self._check_intake_success,
            {
                "success": "vision_analysis",
                "error": "error_handler"
            }
        )
        
        return workflow
    
    async def _intake_node(self, state: DocumentState) -> Dict[str, Any]:
        """Document intake node"""
        logger.info(f"Starting intake for {state.get('filename')}")
        
        try:
            result = await self.intake_agent.execute({
                "file_path": state["file_path"]
            })
            
            if result["success"]:
                data = result["result"]
                return {
                    "metadata": data["metadata"],
                    "text_content": data["text_content"],
                    "text_preview": data["text_preview"],
                    "preview_images": data["preview_images"],
                    "processing_stage": "intake_complete",
                    "messages": [f"Intake completed for {state['filename']}"]
                }
            else:
                return {
                    "error": result.get("error", "Intake failed"),
                    "processing_stage": "intake_failed"
                }
        except Exception as e:
            logger.error(f"Intake node error: {e}")
            return {
                "error": str(e),
                "processing_stage": "intake_failed"
            }
    
    async def _vision_node(self, state: DocumentState) -> Dict[str, Any]:
        """Vision analysis node"""
        logger.info(f"Starting vision analysis for {state.get('filename')}")
        
        try:
            result = await self.vision_agent.execute({
                "preview_images": state.get("preview_images", []),
                "filename": state.get("filename"),
                "metadata": state.get("metadata", {})
            })
            
            if result["success"]:
                return {
                    "vision_analysis": result["result"],
                    "messages": [f"Vision analysis completed"]
                }
            else:
                # Non-critical failure, continue with empty vision analysis
                logger.warning(f"Vision analysis failed: {result.get('error')}")
                return {
                    "vision_analysis": {
                        "visual_domain_hints": [],
                        "confidence": 0.0,
                        "error": result.get("error")
                    },
                    "messages": [f"Vision analysis failed, continuing with text only"]
                }
        except Exception as e:
            logger.error(f"Vision node error: {e}")
            return {
                "vision_analysis": {"error": str(e)},
                "messages": [f"Vision analysis error: {str(e)}"]
            }
    
    async def _text_node(self, state: DocumentState) -> Dict[str, Any]:
        """Text classification node"""
        logger.info(f"Starting text classification for {state.get('filename')}")
        
        try:
            result = await self.text_agent.execute({
                "text_content": state.get("text_content", ""),
                "filename": state.get("filename"),
                "metadata": state.get("metadata", {})
            })
            
            if result["success"]:
                return {
                    "text_analysis": result["result"],
                    "messages": [f"Text classification completed"]
                }
            else:
                return {
                    "text_analysis": {
                        "primary_domain": "general",
                        "confidence": 0.3,
                        "error": result.get("error")
                    },
                    "messages": [f"Text classification failed"]
                }
        except Exception as e:
            logger.error(f"Text node error: {e}")
            return {
                "text_analysis": {
                    "primary_domain": "general",
                    "confidence": 0.3,
                    "error": str(e)
                },
                "messages": [f"Text classification error: {str(e)}"]
            }
    
    async def _router_node(self, state: DocumentState) -> Dict[str, Any]:
        """Domain router decision node"""
        logger.info(f"Starting domain routing for {state.get('filename')}")
        
        # Wait for both vision and text analysis to complete
        vision_analysis = state.get("vision_analysis", {})
        text_analysis = state.get("text_analysis", {})
        
        if not vision_analysis or not text_analysis:
            logger.warning("Waiting for analysis to complete")
            return {}
        
        try:
            result = await self.router_agent.execute({
                "filename": state.get("filename"),
                "vision_analysis": vision_analysis,
                "text_analysis": text_analysis,
                "metadata": state.get("metadata", {})
            })
            
            if result["success"]:
                decision = result["result"]
                return {
                    "final_decision": decision,
                    "final_domain": decision.get("final_domain", "general"),
                    "confidence": decision.get("confidence", 0.0),
                    "messages": [f"Classified as {decision.get('final_domain')} with {decision.get('confidence'):.2f} confidence"]
                }
            else:
                # Fallback to text analysis domain
                return {
                    "final_decision": {"error": result.get("error")},
                    "final_domain": text_analysis.get("primary_domain", "general"),
                    "confidence": 0.5,
                    "messages": [f"Router failed, using text classification"]
                }
        except Exception as e:
            logger.error(f"Router node error: {e}")
            return {
                "final_decision": {"error": str(e)},
                "final_domain": "general",
                "confidence": 0.3,
                "messages": [f"Router error: {str(e)}"]
            }
    
    async def _organization_node(self, state: DocumentState) -> Dict[str, Any]:
        """File organization node"""
        logger.info(f"Starting file organization for {state.get('filename')}")
        
        try:
            result = await self.org_agent.execute({
                "file_path": state["file_path"],
                "filename": state["filename"],
                "domain": state.get("final_domain", "general"),
                "operation": "copy"  # Default to copy to preserve original
            })
            
            if result["success"]:
                org_result = result["result"]
                return {
                    "organization_result": org_result,
                    "output_path": org_result.get("destination", ""),
                    "processing_stage": "completed",
                    "messages": [f"File organized to {state.get('final_domain')} folder"]
                }
            else:
                return {
                    "organization_result": {"error": result.get("error")},
                    "processing_stage": "organization_failed",
                    "error": result.get("error", "Organization failed")
                }
        except Exception as e:
            logger.error(f"Organization node error: {e}")
            return {
                "organization_result": {"error": str(e)},
                "processing_stage": "organization_failed",
                "error": str(e)
            }
    
    async def _error_node(self, state: DocumentState) -> Dict[str, Any]:
        """Error handling node"""
        logger.error(f"Error occurred: {state.get('error')}")
        return {
            "processing_stage": "failed",
            "messages": [f"Processing failed: {state.get('error')}"]
        }
    
    def _check_intake_success(self, state: DocumentState) -> str:
        """Check if intake was successful"""
        if state.get("error"):
            return "error"
        return "success"
    
    async def process_document(self, file_path: str) -> Dict[str, Any]:
        """Process a single document through the workflow"""
        from pathlib import Path
        
        initial_state = {
            "file_path": file_path,
            "filename": Path(file_path).name,
            "messages": []
        }
        
        try:
            # Run the workflow
            final_state = await self.app.ainvoke(initial_state)
            
            return {
                "success": final_state.get("processing_stage") == "completed",
                "filename": final_state.get("filename"),
                "domain": final_state.get("final_domain"),
                "confidence": final_state.get("confidence"),
                "output_path": final_state.get("output_path"),
                "final_decision": final_state.get("final_decision"),
                "messages": final_state.get("messages", [])
            }
        except Exception as e:
            logger.error(f"Workflow execution error: {e}")
            return {
                "success": False,
                "filename": Path(file_path).name,
                "error": str(e)
            }


# Global workflow instance
workflow = DocumentClassificationWorkflow()