import pytest
import asyncio
from typing import Generator, AsyncGenerator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import tempfile
import os
from pathlib import Path

from brandgpt.api.main import app
from brandgpt.models import Base, get_db
from brandgpt.config import settings

# Import mocks - this will auto-enable them via the autouse fixture
from tests.test_config import mock_external_services


# Override settings for testing
settings.database_url = "sqlite:///:memory:"
settings.api_reload = False


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def test_db():
    """Create a test database for each test function."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    yield TestingSessionLocal()
    
    # Clean up
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def client(test_db):
    """Create a test client for the FastAPI app."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="function")
def test_user_credentials():
    """Provide test user credentials."""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123"
    }


@pytest.fixture(scope="function")
def authenticated_client(client, test_user_credentials):
    """Create an authenticated test client."""
    # Register user
    response = client.post("/api/auth/register", json=test_user_credentials)
    assert response.status_code == 200
    
    # Login
    login_data = {
        "username": test_user_credentials["username"],
        "password": test_user_credentials["password"]
    }
    response = client.post(
        "/api/auth/token",
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    
    # Add authentication header
    client.headers["Authorization"] = f"Bearer {token}"
    return client


@pytest.fixture(scope="function")
def test_session(authenticated_client):
    """Create a test session."""
    response = authenticated_client.post(
        "/api/sessions",
        json={"system_prompt": "You are a helpful assistant"}
    )
    assert response.status_code == 200
    return response.json()


@pytest.fixture(scope="session")
def sample_pdf_path():
    """Create a sample PDF file for testing."""
    import reportlab
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.pdf', delete=False) as f:
        pdf_path = f.name
    
    # Create a simple PDF
    c = canvas.Canvas(pdf_path, pagesize=letter)
    c.setFont("Helvetica", 12)
    c.drawString(100, 750, "Test PDF Document")
    c.drawString(100, 730, "This is a test document for the BrandGPT RAG system.")
    c.drawString(100, 710, "It contains sample content about artificial intelligence.")
    c.drawString(100, 690, "Machine learning is a subset of AI that enables computers")
    c.drawString(100, 670, "to learn from data without being explicitly programmed.")
    c.save()
    
    yield pdf_path
    
    # Cleanup
    os.unlink(pdf_path)


@pytest.fixture(scope="session")
def sample_text_content():
    """Provide sample text content for testing."""
    return """
    Natural Language Processing (NLP) is a branch of artificial intelligence
    that helps computers understand, interpret and manipulate human language.
    NLP draws from many disciplines, including computer science and computational
    linguistics, in its pursuit to fill the gap between human communication
    and computer understanding.
    
    Key applications of NLP include:
    - Text classification and categorization
    - Named entity recognition
    - Sentiment analysis
    - Machine translation
    - Question answering systems
    """


@pytest.fixture(scope="session")
def sample_json_content():
    """Provide sample JSON content for testing."""
    return {
        "topic": "Deep Learning",
        "description": "Deep learning is a subset of machine learning that uses neural networks with multiple layers.",
        "applications": [
            "Computer Vision",
            "Natural Language Processing",
            "Speech Recognition",
            "Autonomous Vehicles"
        ],
        "frameworks": {
            "tensorflow": "Google's open-source ML framework",
            "pytorch": "Facebook's deep learning framework",
            "keras": "High-level neural networks API"
        }
    }


@pytest.fixture(scope="function")
def mock_url_server():
    """Create a mock HTTP server for URL testing."""
    from http.server import HTTPServer, SimpleHTTPRequestHandler
    import threading
    
    # Create temporary HTML content
    html_content = """
    <html>
    <head><title>Test Page</title></head>
    <body>
        <h1>Quantum Computing</h1>
        <p>Quantum computing is a type of computation that harnesses the phenomena 
        of quantum mechanics to process information.</p>
        <p>Unlike classical computers that use bits, quantum computers use quantum bits or qubits.</p>
        <a href="/page2.html">Learn more</a>
    </body>
    </html>
    """
    
    html_content_2 = """
    <html>
    <head><title>Test Page 2</title></head>
    <body>
        <h1>Quantum Applications</h1>
        <p>Quantum computers have potential applications in cryptography, drug discovery, 
        and optimization problems.</p>
    </body>
    </html>
    """
    
    # Create temporary directory with HTML files
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "index.html"), "w") as f:
            f.write(html_content)
        with open(os.path.join(tmpdir, "page2.html"), "w") as f:
            f.write(html_content_2)
        
        # Start server in thread
        os.chdir(tmpdir)
        server = HTTPServer(('localhost', 8888), SimpleHTTPRequestHandler)
        thread = threading.Thread(target=server.serve_forever)
        thread.daemon = True
        thread.start()
        
        yield "http://localhost:8888"
        
        server.shutdown()