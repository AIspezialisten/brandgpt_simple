from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
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
    return {"status": "healthy"}


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
@app.post("/api/ingest/file/{session_id}", response_model=schemas.IngestionStatus)
async def ingest_file(
    background_tasks: BackgroundTasks,
    session_id: str,
    file: UploadFile = File(...),
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
    
    # Determine content type
    content_type = "pdf" if file.filename.endswith(".pdf") else "text"
    
    # Create document record
    document = Document(
        session_id=session_id,
        filename=file.filename,
        content_type=content_type
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    
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
        current_user.id,
        db
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
    
    # Create document record
    document = Document(
        session_id=data.session_id,
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
        data.max_depth,
        db
    )
    
    return schemas.IngestionStatus(
        document_id=document.id,
        status="processing",
        message="URL ingestion started"
    )


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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "brandgpt.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload
    )