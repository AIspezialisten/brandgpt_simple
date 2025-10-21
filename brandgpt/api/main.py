from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional, Any, Annotated
import uuid
import logging
from datetime import timedelta

from brandgpt.api import schemas
from brandgpt.api.auth import (
    authenticate_user,
    create_access_token,
    get_current_user,
    get_password_hash
)
from brandgpt.models import get_db, User, Session as DBSession, Prompt, Document
from brandgpt.config import settings
from brandgpt.ingestion import IngestionPipeline
from brandgpt.retrieval import RAGGraph

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="BrandGPT API",
    description="RAG application with PDF, text, and URL ingestion",
    version="0.1.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
ingestion_pipeline = IngestionPipeline()
rag_graph = RAGGraph()


@app.get("/health")
async def health_check():
    """Enhanced health check that validates Ollama models availability."""
    try:
        # Check if required Ollama models are available
        import subprocess
        import json
        
        # Get list of available models
        result = subprocess.run(
            ["curl", "-s", f"{settings.ollama_embedding_url}/api/tags"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            try:
                models_data = json.loads(result.stdout)
                available_models = [model["name"] for model in models_data.get("models", [])]
                
                required_models = [
                    settings.ollama_embedding_model,
                    settings.ollama_llm_model
                ]
                
                missing_models = [model for model in required_models if model not in available_models]
                
                if missing_models:
                    return {
                        "status": "degraded",
                        "message": f"Missing Ollama models: {missing_models}",
                        "available_models": available_models,
                        "required_models": required_models
                    }
                
                return {
                    "status": "healthy",
                    "ollama_models": {
                        "embedding": settings.ollama_embedding_model,
                        "llm": settings.ollama_llm_model,
                        "available": True
                    }
                }
            except (json.JSONDecodeError, KeyError):
                pass
        
        # Fallback - basic health check
        return {
            "status": "healthy",
            "ollama_models": "not_checked"
        }
        
    except Exception as e:
        logger.warning(f"Health check error: {str(e)}")
        return {
            "status": "healthy",
            "ollama_models": "error"
        }


# Authentication endpoints
@app.post("/api/auth/register", response_model=schemas.UserResponse)
async def register(
    user_data: schemas.UserCreate,
    db: Session = Depends(get_db)
):
    # Check if user exists
    existing_user = db.query(User).filter(
        (User.username == user_data.username) | (User.email == user_data.email)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered"
        )
    
    # Create new user
    user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user


@app.post("/api/auth/token", response_model=schemas.Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/api/auth/api-key", response_model=schemas.ApiKeyResponse)
async def generate_api_key(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db)
):
    """Generate API key directly with username/password (no JWT required)."""
    # Authenticate user with username/password
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Generate new API key
    api_key = User.generate_api_key()
    
    # Update user with new API key
    user.api_key = api_key
    db.commit()
    
    return {
        "api_key": api_key,
        "message": "API key generated successfully. Store it securely - it won't be shown again."
    }


@app.get("/api/auth/me", response_model=schemas.UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user info (works with both JWT and API key)."""
    return current_user


# Session endpoints
@app.post("/api/sessions", response_model=schemas.SessionResponse)
async def create_session(
    session_data: schemas.SessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    session = DBSession(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        prompt_id=session_data.prompt_id,
        system_prompt=session_data.system_prompt
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    
    return session


@app.get("/api/sessions", response_model=List[schemas.SessionResponse])
async def list_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    sessions = db.query(DBSession).filter(DBSession.user_id == current_user.id).all()
    return sessions


@app.delete("/api/sessions/{session_id}")
async def delete_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a session and its associated temporary documents.

    This endpoint:
    1. Verifies the session belongs to the current user
    2. Deletes documents that were uploaded to this session WITHOUT a group_id (temporary documents)
    3. Preserves documents that have a group_id (persistent documents)
    4. Deletes the session itself
    """
    from brandgpt.core.vector_store import VectorStore

    # Verify session belongs to user
    session = db.query(DBSession).filter(
        DBSession.id == session_id,
        DBSession.user_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    # Find temporary documents (session_id exists, but group_id is NULL)
    temp_documents = db.query(Document).filter(
        Document.session_id == session_id,
        Document.user_id == current_user.id,
        Document.group_id == None
    ).all()

    # Delete vectors for temporary documents
    vector_store = VectorStore()
    deleted_doc_count = 0

    for document in temp_documents:
        try:
            await vector_store.delete_by_document_id(document.id)
            logger.info(f"Deleted vectors for temporary document {document.id}")
        except Exception as e:
            logger.error(f"Failed to delete vectors for document {document.id}: {str(e)}")

    # Delete temporary documents from database
    for document in temp_documents:
        db.delete(document)
        deleted_doc_count += 1

    # Delete the session
    db.delete(session)
    db.commit()

    return {
        "message": f"Session deleted successfully",
        "session_id": session_id,
        "deleted_documents": deleted_doc_count
    }


# Prompt endpoints
@app.post("/api/prompts", response_model=schemas.PromptResponse)
async def create_prompt(
    prompt_data: schemas.PromptCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    prompt = Prompt(
        name=prompt_data.name,
        description=prompt_data.description,
        content=prompt_data.content,
        created_by=current_user.id
    )
    db.add(prompt)
    db.commit()
    db.refresh(prompt)
    
    return prompt


@app.get("/api/prompts", response_model=List[schemas.PromptResponse])
async def list_prompts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    prompts = db.query(Prompt).all()
    return prompts


# Ingestion endpoints
@app.post("/api/ingest/file", response_model=schemas.IngestionStatus)
async def ingest_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    group_id: Optional[str] = Form(None),
    session_id: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    logger.info(f"=== FILE INGESTION DEBUG ===")
    logger.info(f"User: {current_user.username} (ID: {current_user.id})")
    logger.info(f"File: {file.filename}")
    logger.info(f"Session ID: {session_id}")
    logger.info(f"Group ID: {group_id}")
    logger.info(f"Database engine: {db.bind}")
    # If session_id is provided, verify it belongs to user
    session = None
    if session_id:
        session = db.query(DBSession).filter(
            DBSession.id == session_id,
            DBSession.user_id == current_user.id
        ).first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
    
    # Determine content type
    content_type = "pdf" if file.filename.endswith(".pdf") else "text"
    
    # Create document record
    logger.info(f"Creating document record...")
    try:
        document = Document(
            user_id=current_user.id,
            session_id=session_id,
            group_id=group_id,
            filename=file.filename,
            content_type=content_type
        )
        logger.info(f"Document object created: {document}")
        db.add(document)
        logger.info(f"Document added to session")
        db.commit()
        logger.info(f"Document committed to database")
        db.refresh(document)
        logger.info(f"Document refreshed, ID: {document.id}")
    except Exception as e:
        logger.error(f"Error creating document record: {str(e)}")
        logger.error(f"Exception type: {type(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise
    
    # Read file content and save temporarily
    import tempfile
    content = await file.read()
    with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as tmp:
        tmp.write(content)
        tmp_path = tmp.name
    
    # Process in background
    background_tasks.add_task(
        ingestion_pipeline.process_file_from_path,
        tmp_path,
        file.filename,
        document.id,
        session_id,
        current_user.id
    )
    
    return schemas.IngestionStatus(
        document_id=document.id,
        status="processing",
        message="File ingestion started"
    )


@app.post("/api/ingest/url", response_model=schemas.IngestionStatus)
async def ingest_url(
    background_tasks: BackgroundTasks,
    data: schemas.DocumentUpload,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # If session_id is provided, verify it belongs to user
    session = None
    if data.session_id:
        session = db.query(DBSession).filter(
            DBSession.id == data.session_id,
            DBSession.user_id == current_user.id
        ).first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
    
    # Create document record
    document = Document(
        user_id=current_user.id,
        session_id=data.session_id,
        group_id=data.group_id,
        url=data.url,
        content_type="url",
        doc_metadata={"max_depth": data.max_depth} if data.max_depth else None
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    
    # Process in background
    background_tasks.add_task(
        ingestion_pipeline.process_url,
        data.url,
        document.id,
        data.session_id,
        current_user.id,
        data.max_depth
    )
    
    return schemas.IngestionStatus(
        document_id=document.id,
        status="processing",
        message="URL ingestion started"
    )


@app.post("/api/ingest/structured", response_model=schemas.StructuredDataResponse)
async def ingest_structured_data(
    data: schemas.StructuredDataIngestion,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Ingest structured data (JSON objects/arrays) with preserved structure.
    Backward compatible with v1 API /v1/ingest-structured endpoint.
    
    Supports:
    - Single objects or arrays of objects
    - Group IDs for content organization
    - Original structure preservation for retrieval
    - Searchable text generation for RAG
    """
    from brandgpt.ingestion.structured_processor import StructuredDataProcessor
    
    # If session_id is provided, verify it belongs to user
    session_id = data.session_id
    if session_id:
        session = db.query(DBSession).filter(
            DBSession.id == session_id,
            DBSession.user_id == current_user.id
        ).first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
    
    # Create document record with group_id support
    doc_metadata = {
        "content_type": "structured",
        "group_id": data.group_id,
        **(data.metadata or {})
    }
    
    document = Document(
        user_id=current_user.id,
        session_id=session_id,
        group_id=data.group_id,
        content_type="structured",
        doc_metadata=doc_metadata
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    
    # Process structured data
    processor = StructuredDataProcessor()
    
    # Count items for response
    items_count = len(data.data) if isinstance(data.data, list) else 1
    
    # Process in background for better performance
    background_tasks.add_task(
        process_structured_data_task,
        processor,
        data.data,
        document.id,
        session_id,
        current_user.id,
        data.group_id
    )
    
    return schemas.StructuredDataResponse(
        document_id=document.id,
        status="processing",
        items_processed=items_count,
        message=f"Processing {items_count} structured items"
    )


async def process_structured_data_task(
    processor,
    data: Any,
    document_id: int,
    session_id: Optional[str],
    user_id: int,
    group_id: Optional[str]
):
    """Background task to process structured data."""
    from brandgpt.models import SessionLocal

    # Create a new database session for this background task
    db = SessionLocal()
    try:
        # Process data
        metadata = {
            "document_id": document_id,
            "user_id": user_id,
            "session_id": session_id,
            "group_id": group_id
        }

        documents = processor.process(data, metadata)

        if documents:
            # Store in vector database
            from brandgpt.core.vector_store import VectorStore
            vector_store = VectorStore()
            await vector_store.add_documents(
                documents=documents,
                session_id=session_id,
                user_id=user_id,
                document_id=document_id,
                group_id=group_id
            )

            # Update document status
            doc = db.query(Document).filter(Document.id == document_id).first()
            if doc:
                doc.status = "completed"
                doc.doc_metadata = {
                    **(doc.doc_metadata or {}),
                    "chunks_created": len(documents)
                }
                db.commit()

            logger.info(f"Structured data ingestion completed: {len(documents)} chunks")
        else:
            logger.error("No documents generated from structured data")

    except Exception as e:
        logger.error(f"Error processing structured data: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        # Update document status to failed
        try:
            doc = db.query(Document).filter(Document.id == document_id).first()
            if doc:
                doc.status = "failed"
                doc.doc_metadata = {**doc.doc_metadata, "error": str(e)}
                db.commit()
        except Exception as db_error:
            logger.error(f"Failed to update document status: {str(db_error)}")
    finally:
        db.close()


# Query endpoint
@app.post("/api/query", response_model=schemas.QueryResponse)
async def query(
    request: schemas.QueryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    system_prompt = None
    
    if request.session_id and request.use_system_prompt:
        # Get session and its prompt
        session = db.query(DBSession).filter(
            DBSession.id == request.session_id,
            DBSession.user_id == current_user.id
        ).first()
        
        if session:
            if session.system_prompt:
                system_prompt = session.system_prompt
            elif session.prompt_id:
                prompt = db.query(Prompt).filter(Prompt.id == session.prompt_id).first()
                if prompt:
                    system_prompt = prompt.content
    
    # Process query through RAG pipeline
    result = await rag_graph.process_query(
        query=request.query,
        user_id=current_user.id,
        group_id=request.group_id,
        session_id=request.session_id,
        system_prompt=system_prompt
    )
    
    return schemas.QueryResponse(**result)


@app.get("/api/documents/{session_id}")
async def list_documents(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify session belongs to user
    session = db.query(DBSession).filter(
        DBSession.id == session_id,
        DBSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    documents = db.query(Document).filter(Document.session_id == session_id).all()
    return documents


@app.get("/api/documents")
async def list_user_documents(
    session_id: Optional[str] = None,
    group_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List documents for the current user with flexible filtering options.

    Parameters:
    - session_id (optional): Filter by specific session
    - group_id (optional): Filter by specific group
    - Both can be combined for more specific filtering
    - If neither provided, returns all user documents

    This supports both session-based and session-independent document retrieval.
    """
    query = db.query(Document).filter(Document.user_id == current_user.id)

    if session_id:
        # Verify session belongs to user
        session = db.query(DBSession).filter(
            DBSession.id == session_id,
            DBSession.user_id == current_user.id
        ).first()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )

        query = query.filter(Document.session_id == session_id)

    if group_id:
        query = query.filter(Document.group_id == group_id)

    documents = query.order_by(Document.created_at.desc()).all()
    return documents


# Debug endpoints
@app.get("/api/debug/qdrant-info")
async def debug_qdrant_info(current_user: User = Depends(get_current_user)):
    """Debug endpoint to check Qdrant connection and collection info."""
    from brandgpt.core.vector_store import VectorStore
    
    try:
        vector_store = VectorStore()
        vector_store._ensure_initialized()
        
        # Get collection info
        collections = vector_store.client.get_collections().collections
        collection_info = None
        
        for collection in collections:
            if collection.name == settings.qdrant_collection_name:
                collection_info = vector_store.client.get_collection(settings.qdrant_collection_name)
                break
        
        # Count total points
        total_points = 0
        user_points = 0
        
        if collection_info:
            # Get total count
            total_points = vector_store.client.count(
                collection_name=settings.qdrant_collection_name
            ).count
            
            # Get user-specific count
            user_count_result = vector_store.client.count(
                collection_name=settings.qdrant_collection_name,
                count_filter={
                    "must": [
                        {"key": "user_id", "match": {"value": current_user.id}}
                    ]
                }
            )
            user_points = user_count_result.count
        
        return {
            "qdrant_url": settings.qdrant_url,
            "collection_name": settings.qdrant_collection_name,
            "collection_exists": collection_info is not None,
            "total_points": total_points,
            "user_points": user_points,
            "user_id": current_user.id,
            "collections": [c.name for c in collections]
        }
        
    except Exception as e:
        logger.error(f"Debug Qdrant info error: {str(e)}")
        return {
            "error": str(e),
            "qdrant_url": settings.qdrant_url,
            "collection_name": settings.qdrant_collection_name
        }


@app.get("/api/debug/search-test")
async def debug_search_test(
    query: str = "test",
    current_user: User = Depends(get_current_user)
):
    """Debug endpoint to test vector search without user filtering."""
    from brandgpt.core.vector_store import VectorStore
    
    try:
        vector_store = VectorStore()
        vector_store._ensure_initialized()
        
        # Test search with user filtering (normal)
        user_results = await vector_store.search(
            query=query,
            user_id=current_user.id,
            limit=10
        )
        
        # Test search without user filtering (debug)
        all_results = await vector_store.search(
            query=query,
            user_id=None,  # No user filtering
            limit=10
        )
        
        return {
            "query": query,
            "user_id": current_user.id,
            "user_filtered_results": len(user_results),
            "all_results": len(all_results),
            "user_results_sample": user_results[:2] if user_results else [],
            "all_results_sample": all_results[:2] if all_results else []
        }
        
    except Exception as e:
        logger.error(f"Debug search test error: {str(e)}")
        return {
            "error": str(e),
            "query": query,
            "user_id": current_user.id
        }


@app.get("/api/debug/embedding-test")
async def debug_embedding_test(
    text: str = "test text",
    current_user: User = Depends(get_current_user)
):
    """Debug endpoint to test embedding service."""
    from brandgpt.core.embeddings import EmbeddingService
    
    try:
        embedding_service = EmbeddingService()
        
        # Test embedding generation
        embedding = await embedding_service.embed_query(text)
        
        return {
            "text": text,
            "embedding_length": len(embedding),
            "embedding_sample": embedding[:5],  # First 5 dimensions
            "ollama_url": settings.ollama_embedding_url,
            "model": settings.ollama_embedding_model
        }
        
    except Exception as e:
        logger.error(f"Debug embedding test error: {str(e)}")
        return {
            "error": str(e),
            "text": text,
            "ollama_url": settings.ollama_embedding_url,
            "model": settings.ollama_embedding_model
        }


# Delete endpoint
@app.delete("/api/data", response_model=schemas.DeleteResponse)
async def delete_data(
    data: schemas.DeleteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete documents and their vector embeddings.
    
    Can delete by:
    - group_id: Delete all documents with this group_id
    - document_id: Delete specific document by ID  
    - session_id: Delete all documents in this session
    
    Only one parameter should be provided.
    """
    from brandgpt.core.vector_store import VectorStore
    
    if not any([data.group_id, data.document_id, data.session_id]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must provide either group_id, document_id, or session_id"
        )
    
    if sum(bool(x) for x in [data.group_id, data.document_id, data.session_id]) > 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only one of group_id, document_id, or session_id should be provided"
        )
    
    # Build query to find documents to delete
    query = db.query(Document).filter(Document.user_id == current_user.id)
    
    if data.group_id:
        query = query.filter(Document.group_id == data.group_id)
        delete_message = f"All documents with group_id '{data.group_id}'"
    elif data.document_id:
        query = query.filter(Document.id == data.document_id)
        delete_message = f"Document with ID {data.document_id}"
    elif data.session_id:
        # Verify session belongs to user
        session = db.query(DBSession).filter(
            DBSession.id == data.session_id,
            DBSession.user_id == current_user.id
        ).first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        query = query.filter(Document.session_id == data.session_id)
        delete_message = f"All documents in session '{data.session_id}'"
    
    # Get documents to delete
    documents_to_delete = query.all()
    
    if not documents_to_delete:
        return schemas.DeleteResponse(
            deleted_count=0,
            message="No documents found to delete"
        )
    
    # Delete from vector store first
    # Delete each document individually by document_id for reliability
    vector_store = VectorStore()
    vector_deletion_errors = []
    for document in documents_to_delete:
        try:
            await vector_store.delete_by_document_id(document.id)
            logger.info(f"Deleted vectors for document {document.id}")
        except Exception as e:
            error_msg = f"Failed to delete vectors for document {document.id}: {str(e)}"
            logger.error(error_msg)
            vector_deletion_errors.append(error_msg)

    if vector_deletion_errors:
        logger.warning(f"Some vector deletions failed: {len(vector_deletion_errors)} errors")
        # Continue with database deletion anyway
    
    # Delete from database
    deleted_count = len(documents_to_delete)
    for document in documents_to_delete:
        db.delete(document)
    
    db.commit()
    
    return schemas.DeleteResponse(
        deleted_count=deleted_count,
        message=f"Successfully deleted {deleted_count} documents: {delete_message}"
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "brandgpt.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload
    )