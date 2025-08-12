from typing import Optional
import tempfile
import os
from fastapi import UploadFile
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from brandgpt.ingestion import PDFProcessor, TextProcessor, URLProcessor, JSONProcessor
from brandgpt.ingestion.enhanced_json_processor import EnhancedJSONProcessor
from brandgpt.core import VectorStore
from brandgpt.models import Document

logger = logging.getLogger(__name__)


class IngestionPipeline:
    def __init__(self):
        self.pdf_processor = PDFProcessor()
        self.text_processor = TextProcessor()
        self.url_processor = URLProcessor()
        self.json_processor = EnhancedJSONProcessor()  # Use enhanced processor
        self.vector_store = VectorStore()
    
    async def process_file_from_path(
        self,
        file_path: str,
        filename: str,
        document_id: int,
        session_id: str,
        user_id: int,
        db: Session
    ):
        try:
            # Update document status
            document = db.query(Document).filter(Document.id == document_id).first()
            if not document:
                return
            
            document.processed = "processing"
            db.commit()
            
            try:
                metadata = {
                    "document_id": document_id,
                    "filename": filename,
                    "session_id": session_id
                }
                
                if filename.lower().endswith('.pdf'):
                    # Process PDF
                    chunks = await self.pdf_processor.process(file_path, metadata)
                    
                    # Store in vector database
                    await self.vector_store.add_documents(chunks, session_id, user_id)
                    
                elif filename.lower().endswith('.json'):
                    # Process JSON with enhanced processor
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    chunks = await self.json_processor.process(content, metadata)
                    
                    # Store in vector database like other content types
                    await self.vector_store.add_documents(chunks, session_id, user_id)
                    
                else:
                    # Process as text (with JSON detection)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Check if content is JSON even if filename doesn't end with .json
                    try:
                        import json
                        json.loads(content.strip())
                        # If parsing succeeds, it's JSON content
                        chunks = await self.json_processor.process(content, metadata)
                        logger.info(f"Detected and processed JSON content in text file: {filename}")
                    except (json.JSONDecodeError, ValueError):
                        # Not JSON, process as regular text
                        chunks = await self.text_processor.process(content, metadata)
                    
                    # Store in vector database
                    await self.vector_store.add_documents(chunks, session_id, user_id)
                
                # Update document status
                document.processed = "completed"
                document.processed_at = datetime.utcnow()
                db.commit()
                
                logger.info(f"Successfully processed file: {filename}")
                
            finally:
                # Clean up temporary file
                os.unlink(file_path)
                
        except Exception as e:
            logger.error(f"Error processing file: {str(e)}")
            document = db.query(Document).filter(Document.id == document_id).first()
            if document:
                document.processed = "failed"
                document.error_message = str(e)
                db.commit()

    async def process_file(
        self,
        file: UploadFile,
        document_id: int,
        session_id: str,
        user_id: int,
        db: Session
    ):
        """Legacy method - save file temporarily and call process_file_from_path"""
        # Save uploaded file temporarily
        content = await file.read()
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        
        await self.process_file_from_path(tmp_path, file.filename, document_id, session_id, user_id, db)
    
    async def process_url(
        self,
        url: str,
        document_id: int,
        session_id: str,
        user_id: int,
        max_depth: Optional[int],
        db: Session
    ):
        try:
            # Update document status
            document = db.query(Document).filter(Document.id == document_id).first()
            if not document:
                return
            
            document.processed = "processing"
            db.commit()
            
            metadata = {
                "document_id": document_id,
                "url": url,
                "session_id": session_id,
                "max_depth": max_depth
            }
            
            # Process URL
            chunks = await self.url_processor.process(url, metadata)
            
            # Store in vector database
            await self.vector_store.add_documents(chunks, session_id, user_id)
            
            # Update document status
            document.processed = "completed"
            document.processed_at = datetime.utcnow()
            db.commit()
            
            logger.info(f"Successfully processed URL: {url}")
            
        except Exception as e:
            logger.error(f"Error processing URL: {str(e)}")
            document = db.query(Document).filter(Document.id == document_id).first()
            if document:
                document.processed = "failed"
                document.error_message = str(e)
                db.commit()