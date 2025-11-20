"""
MCP Client for agents to interact with file system operations
"""

import httpx
from typing import Dict, Any
from loguru import logger
from config.settings import settings


class MCPClient:
    """Client for interacting with MCP File Operations Server"""
    
    def __init__(self):
        self.base_url = f"http://{settings.mcp_server_host}:{settings.mcp_server_port}"
        self.timeout = 30.0
    
    async def create_domain_folder(self, domain: str) -> Dict[str, Any]:
        """Create a folder for a specific domain"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/mcp/create_folder",
                    params={"domain": domain}
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"MCP client error creating folder: {e}")
            return {"success": False, "message": str(e)}
    
    async def move_file(self, source_path: str, domain: str, filename: str) -> Dict[str, Any]:
        """Move a file to the appropriate domain folder"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/mcp/move_file",
                    params={
                        "source_path": source_path,
                        "domain": domain,
                        "filename": filename
                    }
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"MCP client error moving file: {e}")
            return {"success": False, "message": str(e)}
    
    async def copy_file(self, source_path: str, domain: str, filename: str) -> Dict[str, Any]:
        """Copy a file to the appropriate domain folder"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/mcp/copy_file",
                    params={
                        "source_path": source_path,
                        "domain": domain,
                        "filename": filename
                    }
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"MCP client error copying file: {e}")
            return {"success": False, "message": str(e)}
    
    async def list_domain_files(self, domain: str) -> Dict[str, Any]:
        """List all files in a domain folder"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/mcp/list_files/{domain}")
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"MCP client error listing files: {e}")
            return {"success": False, "message": str(e)}
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get folder statistics"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/mcp/statistics")
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"MCP client error getting statistics: {e}")
            return {"success": False, "message": str(e)}
    
    async def health_check(self) -> bool:
        """Check if MCP server is healthy"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except Exception as e:
            logger.error(f"MCP server health check failed: {e}")
            return False


# Global MCP client instance
mcp_client = MCPClient()