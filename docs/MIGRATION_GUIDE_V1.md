# Migration Guide: BrandGPT v1 to v2

This guide helps users migrate from BrandGPT v1 (BrandGPT2) to the new v2 implementation.

## Overview of Changes

The new BrandGPT v2 is a complete rewrite with enhanced capabilities:
- **Modern RAG Pipeline**: LangGraph-based orchestration with advanced retrieval
- **User-Scoped Content**: Improved security and multi-user support
- **Enhanced Ingestion**: Support for PDF, URL (with depth), JSON, and structured data
- **Dual Authentication**: Both JWT (for web apps) and API keys (for servers)

## Authentication Changes

### v1 Authentication
```python
# v1: Simple API token
headers = {
    "Authorization": "Bearer YOUR_API_TOKEN"
}
```

### v2 Authentication Options

#### Option 1: API Key Authentication (Recommended for Servers)
```python
# First, register a user and generate API key
import requests

# Register user (one-time)
register_data = {
    "username": "server_user",
    "email": "server@company.com",
    "password": "secure_password_123"
}
response = requests.post("http://api.example.com/api/auth/register", json=register_data)

# Login to get JWT (for API key generation)
login_data = {"username": "server_user", "password": "secure_password_123"}
token_response = requests.post(
    "http://api.example.com/api/auth/token",
    data=login_data,
    headers={"Content-Type": "application/x-www-form-urlencoded"}
)
jwt_token = token_response.json()["access_token"]

# Generate API key (one-time)
api_key_response = requests.post(
    "http://api.example.com/api/auth/api-key",
    headers={"Authorization": f"Bearer {jwt_token}"}
)
api_key = api_key_response.json()["api_key"]  # Save this securely!

# Use API key for all future requests
headers = {
    "Authorization": f"Bearer {api_key}"  # or just api_key without Bearer
}
```

#### Option 2: JWT Authentication (For Web Applications)
```python
# Login each session
login_data = {"username": "user", "password": "password"}
response = requests.post(
    "http://api.example.com/api/auth/token",
    data=login_data,
    headers={"Content-Type": "application/x-www-form-urlencoded"}
)
jwt_token = response.json()["access_token"]

headers = {
    "Authorization": f"Bearer {jwt_token}"
}
```

## Endpoint Mapping

### 1. Structured Data Ingestion

#### v1 Endpoint
```python
# v1: /v1/ingest-structured
data = {
    "objects": [
        {"id": 1, "name": "Product A", "price": 99.99},
        {"id": 2, "name": "Product B", "price": 149.99}
    ],
    "group_id": "products_2024"
}
response = requests.post(
    "http://api.example.com/v1/ingest-structured",
    json=data,
    headers=headers
)
```

#### v2 Endpoint
```python
# v2: /api/ingest/structured
data = {
    "data": [  # Note: "data" field instead of "objects"
        {"id": 1, "name": "Product A", "price": 99.99},
        {"id": 2, "name": "Product B", "price": 149.99}
    ],
    "group_id": "products_2024",  # Still supported!
    "session_id": None,  # Optional, can be None for user-scoped
    "metadata": {  # Additional metadata if needed
        "source": "product_catalog",
        "version": "2024.1"
    }
}
response = requests.post(
    "http://api.example.com/api/ingest/structured",
    json=data,
    headers=headers
)
```

### 2. Group ID Support

While v2 doesn't have built-in group tables, group_id is preserved in metadata:

#### v1: Query with Group ID
```python
# v1: Implicit group filtering
query_data = {
    "query": "What products are available?",
    "group_id": "products_2024"
}
```

#### v2: Query with Group ID
```python
# v2: Explicit group_id in query
query_data = {
    "query": "What products are available?",
    "group_id": "products_2024",  # Filters results by group
    "session_id": None,  # Optional
    "use_system_prompt": False
}
response = requests.post(
    "http://api.example.com/api/query",
    json=query_data,
    headers=headers
)
```

### 3. File Upload

#### v1 Endpoint
```python
# v1: /v1/upload
files = {"file": open("document.pdf", "rb")}
data = {"group_id": "documents_2024"}
response = requests.post(
    "http://api.example.com/v1/upload",
    files=files,
    data=data,
    headers=headers
)
```

#### v2 Endpoint
```python
# v2: /api/ingest/file
files = {"file": open("document.pdf", "rb")}
# Note: group_id goes in metadata through session or structured endpoint
data = {
    "session_id": "optional-session-id",  # Can be None
    "content_type": "pdf"  # Explicitly specify type
}
response = requests.post(
    "http://api.example.com/api/ingest/file",
    files=files,
    data=data,
    headers=headers
)
```

## Key Differences to Note

### 1. User-Scoped Content
- **v1**: Content was globally accessible with API token
- **v2**: Content is scoped to users for better security
- **Impact**: Each API key/user has isolated content

### 2. Session Management
- **v1**: No session concept
- **v2**: Optional sessions for conversation context
- **Recommendation**: Use `session_id: null` for simple v1-like behavior

### 3. Content Types
- **v1**: Automatic detection
- **v2**: Explicit content_type required ("pdf", "text", "url", "json", "structured")

### 4. Background Processing
- **v1**: Synchronous processing
- **v2**: Asynchronous with background tasks
- **Impact**: Better performance but check status endpoint for completion

## Migration Checklist

- [ ] **Authentication**
  - [ ] Register users for v2 system
  - [ ] Generate API keys for server-to-server communication
  - [ ] Update authentication headers in your code

- [ ] **Endpoints**
  - [ ] Update `/v1/ingest-structured` to `/api/ingest/structured`
  - [ ] Update `/v1/upload` to `/api/ingest/file`
  - [ ] Update `/v1/query` to `/api/query`

- [ ] **Data Structure**
  - [ ] Change `objects` field to `data` in structured ingestion
  - [ ] Add `content_type` field where required
  - [ ] Include `group_id` in appropriate metadata fields

- [ ] **Error Handling**
  - [ ] Handle 401 for authentication failures
  - [ ] Check document processing status for async operations
  - [ ] Implement retry logic for background tasks

## Quick Migration Script

```python
class BrandGPTv2Client:
    """Drop-in replacement for v1 client with v2 compatibility."""
    
    def __init__(self, base_url, api_key=None, username=None, password=None):
        self.base_url = base_url
        self.headers = {}
        
        if api_key:
            # Use API key directly
            self.headers["Authorization"] = f"Bearer {api_key}"
        elif username and password:
            # Get JWT token
            self._authenticate(username, password)
    
    def _authenticate(self, username, password):
        """Get JWT token for session."""
        response = requests.post(
            f"{self.base_url}/api/auth/token",
            data={"username": username, "password": password},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        response.raise_for_status()
        token = response.json()["access_token"]
        self.headers["Authorization"] = f"Bearer {token}"
    
    def ingest_structured(self, objects, group_id=None):
        """v1-compatible structured data ingestion."""
        data = {
            "data": objects,  # v2 uses "data" instead of "objects"
            "group_id": group_id,
            "session_id": None  # User-scoped, not session-scoped
        }
        response = requests.post(
            f"{self.base_url}/api/ingest/structured",
            json=data,
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def query(self, query_text, group_id=None):
        """v1-compatible query."""
        data = {
            "query": query_text,
            "group_id": group_id,
            "use_system_prompt": False
        }
        response = requests.post(
            f"{self.base_url}/api/query",
            json=data,
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

# Usage example
client = BrandGPTv2Client(
    base_url="http://api.example.com",
    api_key="bgpt_your_api_key_here"  # Use API key for server-to-server
)

# Ingest structured data (v1-compatible)
client.ingest_structured(
    objects=[{"id": 1, "name": "Product A", "price": 99.99}],
    group_id="products_2024"
)

# Query (v1-compatible)
result = client.query(
    "What products are available?",
    group_id="products_2024"
)
print(result["response"])
```

## Support

For questions or issues during migration:
1. Check the main [README.md](../README.md) for detailed API documentation
2. Review test examples in the `tests/` directory
3. Open an issue on GitHub for specific migration problems

## Benefits of Upgrading

1. **Better Performance**: Async processing and optimized RAG pipeline
2. **Enhanced Security**: User-scoped content isolation
3. **More Features**: URL depth scraping, AI personas, reranking
4. **Flexible Auth**: Support for both JWT and API keys
5. **Production Ready**: Docker deployment with comprehensive testing

The migration effort is worth it for the improved capabilities and performance!