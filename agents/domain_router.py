"""
Domain Router Agent - Orchestrates analysis and makes final classification decisions
"""

from typing import Dict, Any
from loguru import logger
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from .base import BaseAgent


class DomainRouterAgent(BaseAgent):
    """
    Orchestrator agent that combines inputs from Vision and Text agents
    to make final domain classification decision
    """
    
    def __init__(self):
        super().__init__(name="DomainRouterAgent")
        self._setup_router_chain()
    
    def _setup_router_chain(self):
        """Setup decision-making chain"""
        
        self.router_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert document classifier tasked with making the final domain classification decision.

You will receive analysis from two specialized agents:
1. Vision Analysis Agent - analyzed visual/layout elements
2. Text Classification Agent - analyzed textual content

Your task is to:
1. Weigh both analyses based on their confidence scores
2. Look for agreement between the two agents
3. Make a final domain classification decision
4. Provide a confidence score and clear reasoning

Available domains:
- finance: Financial documents, banking, investments, accounting
- law: Legal documents, contracts, court filings
- science: Research papers, scientific studies, experiments
- technology: Technical documentation, software, IT
- healthcare: Medical documents, clinical records, pharmaceutical
- education: Academic materials, curricula, educational content
- business: Business plans, corporate documents, management
- engineering: Engineering designs, specifications, technical drawings
- arts: Creative works, artistic documentation
- general: Documents that don't fit other categories

Response format (JSON):
{{
    "final_domain": "domain_name",
    "confidence": 0.90,
    "reasoning": "Detailed explanation of decision",
    "agreement_level": "high|medium|low",
    "primary_evidence": "key factors that led to decision"
}}"""),
            ("human", """Make a final classification decision based on these analyses:

Filename: {filename}

Vision Analysis:
- Domain hints: {vision_domains}
- Document type: {doc_type}
- Has tables: {has_tables}
- Has charts: {has_charts}
- Confidence: {vision_confidence}

Text Classification:
- Primary domain: {text_domain}
- Confidence: {text_confidence}
- Keywords: {keywords}
- Reasoning: {text_reasoning}

Please provide your final classification.""")
        ])
        
        self.chain = self.router_prompt | self.llm | JsonOutputParser()
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make final domain classification decision
        
        Args:
            input_data: {
                "filename": str,
                "vision_analysis": Dict,
                "text_analysis": Dict,
                "metadata": Dict
            }
        
        Returns:
            Dict with final classification decision
        """
        filename = input_data.get("filename", "unknown")
        vision_analysis = input_data.get("vision_analysis", {})
        text_analysis = input_data.get("text_analysis", {})
        
        # Extract relevant information
        vision_domains = vision_analysis.get("visual_domain_hints", [])
        vision_confidence = vision_analysis.get("confidence", 0.0)
        doc_type = vision_analysis.get("document_type", "unknown")
        has_tables = vision_analysis.get("has_tables", False)
        has_charts = vision_analysis.get("has_charts", False)
        
        text_domain = text_analysis.get("primary_domain", "general")
        text_confidence = text_analysis.get("confidence", 0.0)
        keywords = text_analysis.get("keywords", [])
        text_reasoning = text_analysis.get("reasoning", "")
        
        # Check for quick agreement
        if text_domain in vision_domains and text_confidence > 0.7:
            logger.info(f"Quick agreement on domain: {text_domain}")
            return {
                "final_domain": text_domain,
                "confidence": (text_confidence + vision_confidence) / 2,
                "reasoning": f"Strong agreement between vision and text analysis on {text_domain} domain",
                "agreement_level": "high",
                "primary_evidence": f"Both analyses indicated {text_domain}",
                "method": "quick_agreement"
            }
        
        # Use LLM for complex decision
        try:
            result = await self.chain.ainvoke({
                "filename": filename,
                "vision_domains": ", ".join(vision_domains) if vision_domains else "none detected",
                "doc_type": doc_type,
                "has_tables": has_tables,
                "has_charts": has_charts,
                "vision_confidence": vision_confidence,
                "text_domain": text_domain,
                "text_confidence": text_confidence,
                "keywords": ", ".join(keywords[:10]),
                "text_reasoning": text_reasoning
            })
            
            result["method"] = "llm_decision"
            return result
            
        except Exception as e:
            logger.error(f"Error in router decision: {e}")
            # Fallback to weighted voting
            return self._fallback_decision(vision_analysis, text_analysis)
    
    def _fallback_decision(self, vision_analysis: Dict, text_analysis: Dict) -> Dict[str, Any]:
        """Fallback decision-making logic"""
        text_domain = text_analysis.get("primary_domain", "general")
        text_confidence = text_analysis.get("confidence", 0.0)
        vision_domains = vision_analysis.get("visual_domain_hints", [])
        vision_confidence = vision_analysis.get("confidence", 0.0)
        
        # Weighted voting: text analysis is typically more reliable
        if text_confidence > 0.6:
            final_domain = text_domain
            confidence = text_confidence * 0.8  # Slightly reduce for fallback method
            agreement = "medium" if text_domain in vision_domains else "low"
        elif vision_domains:
            final_domain = vision_domains[0]
            confidence = vision_confidence * 0.7
            agreement = "low"
        else:
            final_domain = "general"
            confidence = 0.4
            agreement = "none"
        
        return {
            "final_domain": final_domain,
            "confidence": confidence,
            "reasoning": f"Fallback decision based on text analysis ({text_confidence}) and vision hints",
            "agreement_level": agreement,
            "primary_evidence": "Text content analysis weighted higher",
            "method": "fallback_weighted"
        }