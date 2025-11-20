"""
File Organization Agent - Manages file system operations via MCP
"""

from typing import Dict, Any
from loguru import logger
from pathlib import Path

from .base import BaseAgent
from mcp.client import mcp_client


class FileOrganizationAgent(BaseAgent):
    """Agent responsible for organizing files using MCP server"""
    
    def __init__(self):
        super().__init__(name="FileOrganizationAgent")
        self.mcp_client = mcp_client
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Organize file into appropriate domain folder
        
        Args:
            input_data: {
                "file_path": str - source file path
                "filename": str
                "domain": str - target domain folder
                "operation": str - "move" or "copy" (default: copy)
            }
        
        Returns:
            Dict with organization results
        """
        file_path = input_data.get("file_path")
        filename = input_data.get("filename")
        domain = input_data.get("domain", "general")
        operation = input_data.get("operation", "copy")
        
        if not file_path or not filename:
            raise ValueError("file_path and filename are required")
        
        # Verify file exists
        if not Path(file_path).exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # First, ensure domain folder exists
        folder_result = await self.mcp_client.create_domain_folder(domain)
        
        if not folder_result.get("success"):
            logger.error(f"Failed to create domain folder: {folder_result.get('message')}")
            return {
                "success": False,
                "error": "Failed to create domain folder",
                "details": folder_result
            }
        
        # Perform file operation
        if operation == "move":
            result = await self.mcp_client.move_file(file_path, domain, filename)
        else:
            result = await self.mcp_client.copy_file(file_path, domain, filename)
        
        if result.get("success"):
            logger.info(f"Successfully {operation}d {filename} to {domain} folder")
            return {
                "success": True,
                "operation": operation,
                "domain": domain,
                "source": file_path,
                "destination": result.get("destination"),
                "message": f"File {operation}d successfully"
            }
        else:
            logger.error(f"File operation failed: {result.get('message')}")
            return {
                "success": False,
                "error": result.get("message"),
                "details": result
            }
    
    async def verify_organization(self, domain: str) -> Dict[str, Any]:
        """Verify files in a domain folder"""
        result = await self.mcp_client.list_domain_files(domain)
        return result
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get organization statistics from MCP server"""
        result = await self.mcp_client.get_statistics()
        return result
    
    async def health_check(self) -> bool:
        """Check if MCP server is healthy"""
        return await self.mcp_client.health_check()