"""
Model Context Protocol (MCP) Server for File System Operations
This server provides tools for managing document files and folders
"""

import os
import shutil
from typing import Dict, Any, List
from pathlib import Path
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from loguru import logger
import uvicorn

app = FastAPI(title="MCP File Operations Server", version="1.0.0")


class FileOperationRequest(BaseModel):
    operation: str
    source_path: str
    destination_path: str = None
    domain: str = None


class FileOperationResponse(BaseModel):
    success: bool
    message: str
    details: Dict[str, Any] = {}


class MCPFileServer:
    """MCP Server for file system operations"""
    
    def __init__(self, base_output_folder: str, base_input_folder: str):
        self.base_output_folder = Path(base_output_folder)
        self.base_input_folder = Path(base_input_folder)
        self._ensure_base_folders()
    
    def _ensure_base_folders(self):
        """Ensure base folders exist"""
        self.base_output_folder.mkdir(parents=True, exist_ok=True)
        self.base_input_folder.mkdir(parents=True, exist_ok=True)
    
    def create_domain_folder(self, domain: str) -> Dict[str, Any]:
        """Create a folder for a specific domain"""
        try:
            domain_path = self.base_output_folder / domain
            domain_path.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"Created/verified domain folder: {domain_path}")
            return {
                "success": True,
                "message": f"Domain folder created: {domain}",
                "path": str(domain_path)
            }
        except Exception as e:
            logger.error(f"Error creating domain folder: {e}")
            return {
                "success": False,
                "message": f"Failed to create domain folder: {str(e)}"
            }
    
    def move_file(self, source_path: str, domain: str, filename: str) -> Dict[str, Any]:
        """Move a file to the appropriate domain folder"""
        try:
            source = Path(source_path)
            if not source.exists():
                return {
                    "success": False,
                    "message": f"Source file not found: {source_path}"
                }
            
            # Create domain folder if it doesn't exist
            domain_folder = self.base_output_folder / domain
            domain_folder.mkdir(parents=True, exist_ok=True)
            
            # Construct destination path
            destination = domain_folder / filename
            
            # Handle duplicate filenames
            if destination.exists():
                base_name = destination.stem
                extension = destination.suffix
                counter = 1
                while destination.exists():
                    destination = domain_folder / f"{base_name}_{counter}{extension}"
                    counter += 1
            
            # Move file
            shutil.move(str(source), str(destination))
            
            logger.info(f"Moved file {filename} to {domain} folder")
            return {
                "success": True,
                "message": f"File moved successfully to {domain}",
                "source": str(source),
                "destination": str(destination)
            }
        except Exception as e:
            logger.error(f"Error moving file: {e}")
            return {
                "success": False,
                "message": f"Failed to move file: {str(e)}"
            }
    
    def copy_file(self, source_path: str, domain: str, filename: str) -> Dict[str, Any]:
        """Copy a file to the appropriate domain folder"""
        try:
            source = Path(source_path)
            if not source.exists():
                return {
                    "success": False,
                    "message": f"Source file not found: {source_path}"
                }
            
            # Create domain folder if it doesn't exist
            domain_folder = self.base_output_folder / domain
            domain_folder.mkdir(parents=True, exist_ok=True)
            
            # Construct destination path
            destination = domain_folder / filename
            
            # Handle duplicate filenames
            if destination.exists():
                base_name = destination.stem
                extension = destination.suffix
                counter = 1
                while destination.exists():
                    destination = domain_folder / f"{base_name}_{counter}{extension}"
                    counter += 1
            
            # Copy file
            shutil.copy2(str(source), str(destination))
            
            logger.info(f"Copied file {filename} to {domain} folder")
            return {
                "success": True,
                "message": f"File copied successfully to {domain}",
                "source": str(source),
                "destination": str(destination)
            }
        except Exception as e:
            logger.error(f"Error copying file: {e}")
            return {
                "success": False,
                "message": f"Failed to copy file: {str(e)}"
            }
    
    def list_domain_files(self, domain: str) -> Dict[str, Any]:
        """List all files in a domain folder"""
        try:
            domain_folder = self.base_output_folder / domain
            if not domain_folder.exists():
                return {
                    "success": True,
                    "message": f"Domain folder does not exist: {domain}",
                    "files": []
                }
            
            files = [f.name for f in domain_folder.iterdir() if f.is_file()]
            
            return {
                "success": True,
                "message": f"Listed files in {domain}",
                "files": files,
                "count": len(files)
            }
        except Exception as e:
            logger.error(f"Error listing files: {e}")
            return {
                "success": False,
                "message": f"Failed to list files: {str(e)}"
            }
    
    def get_folder_statistics(self) -> Dict[str, Any]:
        """Get statistics about all domain folders"""
        try:
            stats = {}
            total_files = 0
            
            for domain_folder in self.base_output_folder.iterdir():
                if domain_folder.is_dir():
                    files = list(domain_folder.glob("*.pdf"))
                    file_count = len(files)
                    total_size = sum(f.stat().st_size for f in files)
                    
                    stats[domain_folder.name] = {
                        "file_count": file_count,
                        "total_size_mb": round(total_size / (1024 * 1024), 2)
                    }
                    total_files += file_count
            
            return {
                "success": True,
                "message": "Statistics retrieved successfully",
                "statistics": stats,
                "total_files": total_files
            }
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {
                "success": False,
                "message": f"Failed to get statistics: {str(e)}"
            }


# Initialize MCP server
mcp_server = MCPFileServer(
    base_output_folder=os.getenv("OUTPUT_BASE_FOLDER", "./output"),
    base_input_folder=os.getenv("INPUT_FOLDER", "./input_pdfs")
)


@app.post("/mcp/create_folder", response_model=FileOperationResponse)
async def create_folder(domain: str):
    """Create a domain folder"""
    result = mcp_server.create_domain_folder(domain)
    return FileOperationResponse(**result)


@app.post("/mcp/move_file", response_model=FileOperationResponse)
async def move_file(source_path: str, domain: str, filename: str):
    """Move a file to a domain folder"""
    result = mcp_server.move_file(source_path, domain, filename)
    return FileOperationResponse(**result)


@app.post("/mcp/copy_file", response_model=FileOperationResponse)
async def copy_file(source_path: str, domain: str, filename: str):
    """Copy a file to a domain folder"""
    result = mcp_server.copy_file(source_path, domain, filename)
    return FileOperationResponse(**result)


@app.get("/mcp/list_files/{domain}")
async def list_files(domain: str):
    """List all files in a domain folder"""
    result = mcp_server.list_domain_files(domain)
    return result


@app.get("/mcp/statistics")
async def get_statistics():
    """Get folder statistics"""
    result = mcp_server.get_folder_statistics()
    return result


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "MCP File Operations Server"}


if __name__ == "__main__":
    port = int(os.getenv("MCP_SERVER_PORT", 8001))
    host = os.getenv("MCP_SERVER_HOST", "0.0.0.0")
    
    logger.info(f"Starting MCP Server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)