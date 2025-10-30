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
        user_id: int
    ):
        from brandgpt.models import SessionLocal

        # Create a new database session for this background task
        db = SessionLocal()
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
                    await self.vector_store.add_documents(
                        documents=chunks, 
                        session_id=session_id, 
                        user_id=user_id, 
                        document_id=document_id,
                        group_id=document.group_id
                    )
                    
                elif filename.lower().endswith('.json'):
                    # Process JSON with enhanced processor
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    chunks = await self.json_processor.process(content, metadata)
                    
                    # Store in vector database like other content types
                    await self.vector_store.add_documents(
                        documents=chunks, 
                        session_id=session_id, 
                        user_id=user_id, 
                        document_id=document_id,
                        group_id=document.group_id
                    )
                    
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
                    await self.vector_store.add_documents(
                        documents=chunks, 
                        session_id=session_id, 
                        user_id=user_id, 
                        document_id=document_id,
                        group_id=document.group_id
                    )
                
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
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            try:
                document = db.query(Document).filter(Document.id == document_id).first()
                if document:
                    document.processed = "failed"
                    document.error_message = str(e)
                    db.commit()
            except Exception as db_error:
                logger.error(f"Failed to update document status: {str(db_error)}")
        finally:
            db.close()

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
        max_depth: Optional[int]
    ):
        import asyncio
        from brandgpt.models import SessionLocal

        # Create a new database session for this background task
        db = SessionLocal()
        try:
            # Update document status to processing and set started_at
            document = db.query(Document).filter(Document.id == document_id).first()
            if not document:
                logger.error(f"Document {document_id} not found")
                return

            document.processed = "processing"
            document.started_at = datetime.utcnow()
            document.doc_metadata = {
                **(document.doc_metadata or {}),
                "phase": "scraping",
                "progress_percent": 0
            }
            db.commit()
            logger.info(f"📄 Processing URL: {url} (document_id: {document_id})")

            metadata = {
                "document_id": document_id,
                "url": url,
                "session_id": session_id,
                "max_depth": max_depth
            }

            # Step 1: Process URL with timeout (10 minutes total)
            logger.info(f"1️⃣ Scraping URL: {url}")
            try:
                chunks = await asyncio.wait_for(
                    self.url_processor.process(url, metadata),
                    timeout=600.0  # 10 minutes for scraping
                )
                logger.info(f"✅ Scraped URL successfully: {len(chunks)} chunks")

                # Update progress after scraping
                document = db.query(Document).filter(Document.id == document_id).first()
                if document:
                    document.doc_metadata = {
                        **(document.doc_metadata or {}),
                        "phase": "embedding",
                        "progress_percent": 30,
                        "chunks_total": len(chunks),
                        "chunks_processed": 0
                    }
                    db.commit()

            except asyncio.TimeoutError:
                raise TimeoutError(f"URL scraping timed out after 600 seconds")
            except Exception as e:
                logger.error(f"❌ URL scraping failed: {str(e)}")
                raise

            # Step 2: Store in vector database with dynamic timeout
            # Calculate timeout based on number of chunks
            # Batch size is 5, ~20 seconds per batch + 120 second buffer
            batch_size = 5
            estimated_batches = (len(chunks) + batch_size - 1) // batch_size
            embedding_timeout = estimated_batches * 20 + 120
            logger.info(f"2️⃣ Generating embeddings and storing {len(chunks)} chunks")
            logger.info(f"   Estimated batches: {estimated_batches}, Timeout: {embedding_timeout}s ({embedding_timeout//60} minutes)")
            try:
                await asyncio.wait_for(
                    self.vector_store.add_documents(
                        documents=chunks,
                        session_id=session_id,
                        user_id=user_id,
                        document_id=document_id,
                        group_id=document.group_id
                    ),
                    timeout=embedding_timeout
                )
                logger.info(f"✅ Stored all chunks in vector database")
            except asyncio.TimeoutError:
                raise TimeoutError(f"Embedding generation timed out after {embedding_timeout} seconds")
            except Exception as e:
                logger.error(f"❌ Embedding/storage failed: {str(e)}")
                raise

            # Update document status to completed
            document = db.query(Document).filter(Document.id == document_id).first()
            if document:
                document.processed = "completed"
                document.processed_at = datetime.utcnow()
                document.doc_metadata = {
                    **(document.doc_metadata or {}),
                    "phase": "completed",
                    "progress_percent": 100
                }
                db.commit()

            logger.info(f"✅ Successfully processed URL: {url} (document_id: {document_id})")

        except Exception as e:
            error_msg = str(e)
            error_type = type(e).__name__
            logger.error(f"❌ Error processing URL: {error_type}: {error_msg}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            try:
                document = db.query(Document).filter(Document.id == document_id).first()
                if document:
                    document.processed = "failed"
                    document.processed_at = datetime.utcnow()
                    # Provide more specific error messages
                    if "TimeoutError" in error_type or "timeout" in error_msg.lower():
                        document.error_message = f"Timeout: {error_msg}"
                    else:
                        document.error_message = f"{error_type}: {error_msg}"
                    # Update metadata with error info
                    document.doc_metadata = {
                        **(document.doc_metadata or {}),
                        "phase": "failed",
                        "error_type": error_type
                    }
                    db.commit()
            except Exception as db_error:
                logger.error(f"Failed to update document status: {str(db_error)}")
        finally:
            db.close()