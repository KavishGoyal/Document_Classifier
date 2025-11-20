"""
Document Intake Agent - Handles PDF ingestion and initial processing
"""

import os
from typing import Dict, Any, List
from pathlib import Path
import PyPDF2
from pdf2image import convert_from_path
from PIL import Image
import io
import base64
from loguru import logger

from .base import BaseAgent
from config.settings import settings


class DocumentIntakeAgent(BaseAgent):
    """Agent responsible for ingesting and preprocessing PDF documents"""
    
    def __init__(self):
        super().__init__(name="DocumentIntakeAgent")
        self.max_pages = settings.max_pages_per_document
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process PDF document and extract metadata
        
        Args:
            input_data: {
                "file_path": str - path to PDF file
            }
        
        Returns:
            Dict with document metadata and extracted content
        """
        file_path = input_data.get("file_path")
        
        if not file_path or not os.path.exists(file_path):
            raise ValueError(f"Invalid file path: {file_path}")
        
        # Extract metadata
        metadata = self._extract_metadata(file_path)
        
        # Extract text
        text_content = self._extract_text(file_path)
        
        # Generate preview images for vision analysis
        preview_images = self._generate_preview_images(file_path)
        
        return {
            "file_path": file_path,
            "filename": os.path.basename(file_path),
            "metadata": metadata,
            "text_content": text_content,
            "text_preview": text_content[:2000] if text_content else "",
            "preview_images": preview_images,
            "processing_stage": "intake_complete"
        }
    
    def _extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract PDF metadata"""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                metadata = {
                    "page_count": len(pdf_reader.pages),
                    "file_size": os.path.getsize(file_path),
                    "file_size_mb": round(os.path.getsize(file_path) / (1024 * 1024), 2)
                }
                
                # Extract PDF info if available
                if pdf_reader.metadata:
                    pdf_info = pdf_reader.metadata
                    metadata["title"] = pdf_info.get("/Title", "")
                    metadata["author"] = pdf_info.get("/Author", "")
                    metadata["subject"] = pdf_info.get("/Subject", "")
                    metadata["creator"] = pdf_info.get("/Creator", "")
                
                return metadata
        except Exception as e:
            logger.error(f"Error extracting metadata: {e}")
            return {
                "page_count": 0,
                "file_size": os.path.getsize(file_path),
                "error": str(e)
            }
    
    def _extract_text(self, file_path: str) -> str:
        """Extract text content from PDF"""
        try:
            text_content = []
            
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                # Limit pages to avoid excessive processing
                max_pages = min(len(pdf_reader.pages), self.max_pages)
                
                for page_num in range(max_pages):
                    page = pdf_reader.pages[page_num]
                    text = page.extract_text()
                    if text:
                        text_content.append(text)
            
            return "\n\n".join(text_content)
        except Exception as e:
            logger.error(f"Error extracting text: {e}")
            return ""
    
    def _generate_preview_images(self, file_path: str, max_pages: int = 3) -> List[str]:
        """Generate base64 encoded preview images from first few pages"""
        try:
            # Convert first few pages to images
            images = convert_from_path(
                file_path,
                first_page=1,
                last_page=min(max_pages, self.max_pages),
                dpi=150,
                fmt='jpeg'
            )
            
            preview_images = []
            for img in images:
                # Resize image to reduce size
                img.thumbnail((800, 1000), Image.Resampling.LANCZOS)
                
                # Convert to base64
                buffer = io.BytesIO()
                img.save(buffer, format='JPEG', quality=85)
                img_str = base64.b64encode(buffer.getvalue()).decode()
                preview_images.append(img_str)
            
            return preview_images
        except Exception as e:
            logger.error(f"Error generating preview images: {e}")
            return []
    
    async def batch_process(self, file_paths: List[str]) -> List[Dict[str, Any]]:
        """Process multiple documents in batch"""
        results = []
        
        for file_path in file_paths:
            try:
                result = await self.execute({"file_path": file_path})
                results.append(result)
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
                results.append({
                    "file_path": file_path,
                    "success": False,
                    "error": str(e)
                })
        
        return results