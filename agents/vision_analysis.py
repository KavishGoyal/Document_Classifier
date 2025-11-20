"""
Vision Analysis Agent - Analyzes document layout and visual elements using Groq Vision
"""

from typing import Dict, Any, List
from loguru import logger
from langchain_core.messages import HumanMessage
from langchain_groq import ChatGroq

from .base import BaseAgent
from config.settings import settings


class VisionAnalysisAgent(BaseAgent):
    """Agent that uses vision models to analyze document layout and visual characteristics"""
    
    def __init__(self):
        super().__init__(
            name="VisionAnalysisAgent",
            model_name=settings.groq_vision_model
        )
        # Initialize vision-capable model
        self.vision_llm = ChatGroq(
            groq_api_key=settings.groq_api_key,
            model_name=settings.groq_vision_model,
            temperature=0.1,
        )
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze document using vision model
        
        Args:
            input_data: {
                "preview_images": List[str] - base64 encoded images
                "filename": str
                "metadata": Dict
            }
        
        Returns:
            Dict with vision analysis results
        """
        preview_images = input_data.get("preview_images", [])
        filename = input_data.get("filename", "unknown")
        
        if not preview_images:
            logger.warning(f"No preview images available for {filename}")
            return {
                "visual_domain_hints": [],
                "document_type": "unknown",
                "has_tables": False,
                "has_charts": False,
                "layout_type": "unknown",
                "confidence": 0.0
            }
        
        # Analyze first page (most representative)
        analysis = await self._analyze_image(preview_images[0], filename)
        
        return analysis
    
    async def _analyze_image(self, image_base64: str, filename: str) -> Dict[str, Any]:
        """Analyze a single document page image"""
        try:
            # Create vision prompt
            prompt = """Analyze this document page and provide insights about its domain and characteristics.

Focus on:
1. **Visual Domain Indicators**: What domain does this document belong to based on visual elements?
   - Look for logos, letterheads, formatting styles
   - Charts, graphs, tables (finance, science)
   - Legal formatting, court headers (law)
   - Medical symbols, prescription formats (healthcare)
   - Code snippets, technical diagrams (technology)
   - Academic formatting, citations (education/science)

2. **Document Type**: Is this a report, contract, research paper, presentation, invoice, etc?

3. **Layout Analysis**:
   - Does it contain tables, charts, or graphs?
   - Is it text-heavy or visual-heavy?
   - What's the overall structure?

4. **Domain Classification**: Based on visual analysis, what are the top 3 most likely domains?

Provide your analysis in a structured format focusing on domain classification."""

            # Create message with image
            message = HumanMessage(
                content=[
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}"
                        }
                    }
                ]
            )
            
            # Get response from vision model
            response = await self.vision_llm.ainvoke([message])
            analysis_text = response.content
            
            # Parse the response to extract structured data
            parsed_analysis = self._parse_vision_response(analysis_text)
            
            return parsed_analysis
            
        except Exception as e:
            logger.error(f"Error in vision analysis: {e}")
            return {
                "visual_domain_hints": [],
                "document_type": "unknown",
                "has_tables": False,
                "has_charts": False,
                "layout_type": "text-heavy",
                "confidence": 0.0,
                "error": str(e)
            }
    
    def _parse_vision_response(self, response_text: str) -> Dict[str, Any]:
        """Parse the vision model response into structured data"""
        # Simple parsing logic - in production, you might want more sophisticated parsing
        response_lower = response_text.lower()
        
        # Detect domain hints
        domain_hints = []
        domains_map = {
            "finance": ["financial", "banking", "investment", "stock", "revenue", "accounting"],
            "law": ["legal", "court", "contract", "attorney", "lawsuit", "statute"],
            "science": ["research", "experiment", "hypothesis", "scientific", "study"],
            "technology": ["software", "code", "algorithm", "system", "technical", "api"],
            "healthcare": ["medical", "patient", "clinical", "diagnosis", "health", "pharmaceutical"],
            "education": ["academic", "university", "course", "student", "curriculum"],
            "business": ["business", "management", "strategy", "corporate", "marketing"],
            "engineering": ["engineering", "design", "construction", "structural", "mechanical"]
        }
        
        for domain, keywords in domains_map.items():
            if any(keyword in response_lower for keyword in keywords):
                domain_hints.append(domain)
        
        # Detect document features
        has_tables = any(word in response_lower for word in ["table", "tabular", "grid"])
        has_charts = any(word in response_lower for word in ["chart", "graph", "diagram", "visualization"])
        
        # Determine layout type
        if has_tables or has_charts:
            layout_type = "visual-heavy"
        elif "text" in response_lower and "heavy" in response_lower:
            layout_type = "text-heavy"
        else:
            layout_type = "mixed"
        
        # Estimate confidence based on number of domain hints
        confidence = min(len(domain_hints) * 0.25, 1.0)
        
        return {
            "visual_domain_hints": domain_hints[:3],  # Top 3 domains
            "document_type": self._extract_document_type(response_lower),
            "has_tables": has_tables,
            "has_charts": has_charts,
            "layout_type": layout_type,
            "confidence": confidence,
            "raw_analysis": response_text[:500]  # Store first 500 chars for reference
        }
    
    def _extract_document_type(self, text: str) -> str:
        """Extract document type from analysis text"""
        doc_types = {
            "report": ["report", "annual report", "quarterly report"],
            "contract": ["contract", "agreement"],
            "research_paper": ["research paper", "academic paper", "journal article"],
            "presentation": ["presentation", "slides", "powerpoint"],
            "invoice": ["invoice", "bill", "receipt"],
            "manual": ["manual", "guide", "handbook"],
            "specification": ["specification", "spec sheet", "datasheet"]
        }
        
        for doc_type, keywords in doc_types.items():
            if any(keyword in text for keyword in keywords):
                return doc_type
        
        return "document"