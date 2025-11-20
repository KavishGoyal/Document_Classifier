"""
Text Classification Agent - Classifies documents based on textual content
"""

from typing import Dict, Any, List, Tuple
from loguru import logger
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from .base import BaseAgent
from config.settings import DOMAIN_KEYWORDS


class TextClassificationAgent(BaseAgent):
    """Agent that classifies documents based on text content analysis"""
    
    def __init__(self):
        super().__init__(name="TextClassificationAgent")
        self.domain_keywords = DOMAIN_KEYWORDS
        self._setup_classification_chain()
    
    def _setup_classification_chain(self):
        """Setup LangChain classification chain"""
        
        # Create domain descriptions for the prompt
        domain_descriptions = "\n".join([
            f"- {domain}: Documents about {', '.join(keywords[:5])}"
            for domain, keywords in self.domain_keywords.items()
        ])
        
        self.classification_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a document classification expert. Analyze the provided document text and classify it into ONE of the following domains:

{domain_descriptions}

Also consider:
- general: Documents that don't fit clearly into other categories

Your task:
1. Analyze the text content carefully
2. Identify key terminology and concepts
3. Determine the primary domain
4. Assign a confidence score (0.0 to 1.0)
5. Extract relevant keywords

Respond in JSON format:
{{
    "primary_domain": "domain_name",
    "confidence": 0.85,
    "reasoning": "Brief explanation",
    "keywords": ["keyword1", "keyword2", ...],
    "alternative_domains": ["domain2", "domain3"]
}}"""),
            ("human", "Document filename: {filename}\n\nDocument text:\n{text}")
        ])
        
        self.chain = self.classification_prompt | self.llm | JsonOutputParser()
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classify document based on text content
        
        Args:
            input_data: {
                "text_content": str - extracted text
                "filename": str
                "metadata": Dict
            }
        
        Returns:
            Dict with classification results
        """
        text_content = input_data.get("text_content", "")
        filename = input_data.get("filename", "unknown")
        
        if not text_content or len(text_content.strip()) < 50:
            logger.warning(f"Insufficient text content for {filename}")
            # Fallback to keyword-based classification
            return self._keyword_based_classification(text_content, filename)
        
        # Limit text length for API
        text_sample = text_content[:8000]  # Use first 8000 chars
        
        try:
            # Use LLM-based classification
            result = await self._llm_classification(text_sample, filename)
            return result
        except Exception as e:
            logger.error(f"LLM classification failed: {e}, falling back to keyword-based")
            return self._keyword_based_classification(text_content, filename)
    
    async def _llm_classification(self, text: str, filename: str) -> Dict[str, Any]:
        """Classify using LLM"""
        try:
            domain_descriptions = "\n".join([
                f"- {domain}: {', '.join(keywords[:5])}"
                for domain, keywords in self.domain_keywords.items()
            ])
            
            result = await self.chain.ainvoke({
                "domain_descriptions": domain_descriptions,
                "text": text,
                "filename": filename
            })
            
            return {
                "primary_domain": result.get("primary_domain", "general"),
                "confidence": result.get("confidence", 0.5),
                "reasoning": result.get("reasoning", ""),
                "keywords": result.get("keywords", []),
                "alternative_domains": result.get("alternative_domains", []),
                "method": "llm"
            }
        except Exception as e:
            logger.error(f"Error in LLM classification: {e}")
            raise
    
    def _keyword_based_classification(self, text: str, filename: str) -> Dict[str, Any]:
        """Fallback keyword-based classification"""
        text_lower = text.lower()
        
        # Count keyword matches for each domain
        domain_scores = {}
        for domain, keywords in self.domain_keywords.items():
            score = sum(1 for keyword in keywords if keyword.lower() in text_lower)
            domain_scores[domain] = score
        
        # Get top domains
        sorted_domains = sorted(domain_scores.items(), key=lambda x: x[1], reverse=True)
        
        if sorted_domains[0][1] == 0:
            # No matches found
            return {
                "primary_domain": "general",
                "confidence": 0.3,
                "reasoning": "No domain-specific keywords found",
                "keywords": [],
                "alternative_domains": [],
                "method": "keyword_fallback"
            }
        
        primary_domain = sorted_domains[0][0]
        primary_score = sorted_domains[0][1]
        
        # Calculate confidence based on score distribution
        total_score = sum(score for _, score in sorted_domains)
        confidence = primary_score / total_score if total_score > 0 else 0.3
        confidence = min(confidence, 0.85)  # Cap at 0.85 for keyword-based
        
        # Extract keywords that matched
        matched_keywords = [
            keyword for keyword in self.domain_keywords[primary_domain]
            if keyword.lower() in text_lower
        ][:10]
        
        return {
            "primary_domain": primary_domain,
            "confidence": confidence,
            "reasoning": f"Found {primary_score} domain-specific keywords",
            "keywords": matched_keywords,
            "alternative_domains": [d for d, _ in sorted_domains[1:3]],
            "method": "keyword_fallback"
        }
    
    def _extract_key_phrases(self, text: str, top_n: int = 10) -> List[str]:
        """Extract key phrases from text (simple implementation)"""
        # Simple word frequency approach
        words = text.lower().split()
        
        # Filter out common words
        common_words = set(['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for'])
        filtered_words = [w for w in words if w not in common_words and len(w) > 3]
        
        # Count frequency
        from collections import Counter
        word_freq = Counter(filtered_words)
        
        return [word for word, _ in word_freq.most_common(top_n)]