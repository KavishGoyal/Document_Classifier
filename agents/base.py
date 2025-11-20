"""
Base Agent class for all specialized agents
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
from loguru import logger
from langchain_groq import ChatGroq
from config.settings import settings
import time


class BaseAgent(ABC):
    """Abstract base class for all agents"""
    
    def __init__(self, name: str, model_name: Optional[str] = None):
        self.name = name
        self.model_name = model_name or settings.groq_text_model
        self.llm = self._initialize_llm()
        self.execution_count = 0
    
    def _initialize_llm(self) -> ChatGroq:
        """Initialize the Groq LLM"""
        return ChatGroq(
            groq_api_key=settings.groq_api_key,
            model_name=self.model_name,
            temperature=0.1,
            max_tokens=2048,
        )
    
    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process input data and return results"""
        pass
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the agent with timing and error handling"""
        start_time = time.time()
        self.execution_count += 1
        
        try:
            logger.info(f"Agent {self.name} starting execution #{self.execution_count}")
            
            result = await self.process(input_data)
            
            execution_time = time.time() - start_time
            
            return {
                "agent_name": self.name,
                "success": True,
                "result": result,
                "execution_time": execution_time,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Agent {self.name} execution failed: {e}")
            
            return {
                "agent_name": self.name,
                "success": False,
                "error": str(e),
                "execution_time": execution_time,
                "timestamp": datetime.now().isoformat()
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get agent statistics"""
        return {
            "name": self.name,
            "model": self.model_name,
            "execution_count": self.execution_count
        }