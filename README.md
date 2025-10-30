# BrandGPT: Intelligent RAG Application

> A complete Retrieval-Augmented Generation (RAG) application with multi-format document ingestion, user-scoped content management, reusable AI personas, and production-ready Docker deployment.

[![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green?logo=fastapi)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue?logo=docker)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

> **📢 Migrating from v1?** See our comprehensive [Migration Guide](docs/MIGRATION_GUIDE_V1.md) for smooth transition to v2 with enhanced features including dual authentication (JWT + API keys) and structured data support.

## 🚀 Quick Start

### Prerequisites
- **Ollama** (required): Install and run with required models
- **Docker & Docker Compose** (for containerized deployment)
- **Python 3.11+** (for local development)

### 1. Setup Ollama (Host System)
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull required models
ollama pull hf.co/Qwen/Qwen3-Embedding-8B-GGUF
ollama pull mistral-small:24b

# Verify Ollama is running
curl http://localhost:11434/api/tags
```

### 2. Deploy with Docker
```bash
git clone https://github.com/AIspezialisten/brandgpt_simple.git
cd brandgpt_simple

# Automated deployment
./deploy.sh

# Or manual deployment
docker-compose up -d
```

### 3. Access Your RAG Application
- **API**: http://localhost:9700
- **Interactive Docs**: http://localhost:9700/docs
- **Health Check**: http://localhost:9700/health

---

## ⚠️ Breaking Changes - Asynchronous Ingestion

**Version 2.1** introduces asynchronous document ingestion for improved reliability and timeout resistance.

### What Changed

**All ingestion endpoints now return immediately with `202 Accepted`:**
- `POST /api/ingest/file` - File upload
- `POST /api/ingest/url` - URL scraping
- `POST /api/ingest/structured` - Structured data

**New status polling endpoint:**
- `GET /api/document/{document_id}` - Poll for processing status (note: singular "document")

### Migration Required

**Before (Synchronous):**
```python
response = requests.post("/api/ingest/url", json=data, headers=headers)
result = response.json()  # Blocks until complete (~90s)
print("Done!")
```

**After (Asynchronous):**
```python
# Step 1: Submit document (returns immediately)
response = requests.post("/api/ingest/url", json=data, headers=headers)
document_id = response.json()['document_id']

# Step 2: Poll for completion
while True:
    status = requests.get(f"/api/document/{document_id}", headers=headers).json()
    if status['processed'] == 'completed':
        break
    time.sleep(3)
```

### Benefits
- ✅ Works with any proxy timeout (even 30s)
- ✅ Real-time progress tracking (phase, percentage)
- ✅ No blocking operations
- ✅ Better user experience with progress visibility

See [Document Ingestion](#-document-ingestion) section for detailed examples.

---

## 📖 Table of Contents

- [🎯 Key Features](#-key-features)
- [🏗️ System Architecture](#️-system-architecture)
- [🔐 Authentication System](#-authentication-system)
- [📚 Document Ingestion](#-document-ingestion)
- [🤖 AI Personas & Prompts](#-ai-personas--prompts)
- [🔍 RAG Query System](#-rag-query-system)
- [🌐 Complete API Reference](#-complete-api-reference)
- [💡 Usage Examples](#-usage-examples)
- [🐳 Docker Deployment](#-docker-deployment)
- [🧪 Testing](#-testing)

---

## 🎯 Key Features

### 🔐 **Dual Authentication System**
- **JWT Tokens**: Secure authentication for web applications
- **API Keys**: Simple authentication for server-to-server communication
- **Backward Compatible**: Support for v1 API patterns with enhanced security

### 📄 **Multi-Format Document Ingestion**
- **PDF Documents**: Extract text, tables, and metadata
- **Web URLs**:
  - Asynchronous crawling with configurable depth (1-10 levels)
  - Smart content extraction removes navigation, ads, and boilerplate (98% chunk reduction)
  - Progress tracking with real-time status updates
  - Works with any proxy timeout configuration
- **Structured Data**: Preserve original JSON structure while enabling RAG
- **JSON Data**: Smart processing with natural language conversion
- **Text Files**: Direct text processing with automatic chunking
- **All Formats**: Asynchronous processing with 202 Accepted pattern for reliability

### 👤 **User-Scoped Content Management**
- **Private Content**: Each user's documents are isolated and secure
- **Group Organization**: Optional group_id for content categorization
- **Cross-Session Access**: Access your content from any session
- **Persistent Storage**: Documents remain available across app restarts
- **Document Lifecycle**: Persistent documents (with group_id) vs temporary (session-scoped only)

### 🎭 **Reusable AI Personas**
- **Prompt Library**: Store and reuse custom system prompts
- **Multiple Personas**: Switch between different AI personalities
- **Consistent Behavior**: Same persona maintains consistent responses
- **Dynamic Switching**: Change prompts mid-session without losing context

### 💬 **Conversation Memory**
- **Chat History**: Automatic storage of all conversation messages
- **Context-Aware Responses**: AI remembers previous messages in the session
- **Message Retrieval**: Access full conversation history via API
- **Multi-Turn Dialogues**: Natural conversations that build on previous context

### 🔄 **Advanced RAG Pipeline**
- **Intelligent Retrieval**: Vector similarity search with user and group filtering
- **Result Reranking**: Improve relevance with cross-encoder models
- **Context Generation**: Smart context preparation for LLM
- **Response Generation**: High-quality responses with source attribution

---

## 🏗️ System Architecture

```mermaid
graph TB
    Client[Client Application] --> API[FastAPI REST API]
    API --> Auth[JWT Authentication]
    API --> Pipeline[Ingestion Pipeline]
    API --> RAG[RAG Query Engine]
    
    Pipeline --> PDF[PDF Processor]
    Pipeline --> URL[URL Scraper]
    Pipeline --> JSON[JSON Processor]
    Pipeline --> Text[Text Processor]
    
    PDF --> Embeddings[Ollama Embeddings]
    URL --> Embeddings
    JSON --> Embeddings
    Text --> Embeddings
    
    Embeddings --> Qdrant[(Qdrant Vector DB)]
    Auth --> SQLite[(SQLite Database)]
    API --> SQLite
    
    RAG --> Retriever[Vector Retriever]
    RAG --> Reranker[Result Reranker]
    RAG --> Generator[LLM Generator]
    
    Retriever --> Qdrant
    Generator --> Ollama[Ollama LLM]
    
    classDef external fill:#e1f5fe;
    classDef storage fill:#f3e5f5;
    classDef processing fill:#e8f5e8;
    
    class Client,Ollama external;
    class SQLite,Qdrant storage;
    class Pipeline,RAG,Embeddings,Reranker processing;
```

### Technology Stack
- **🌐 API Framework**: FastAPI with automatic OpenAPI docs
- **🤖 LLM Integration**: Ollama (Mistral-Small-24B for generation)
- **🔤 Embeddings**: Qwen3-Embedding-8B-GGUF via Ollama
- **🗃️ Vector Database**: Qdrant for high-performance similarity search
- **💾 Metadata Storage**: SQLite for users, sessions, and documents
- **🔄 Workflow Orchestration**: LangGraph for RAG pipeline
- **🐳 Deployment**: Docker with host networking for optimal performance

---

## 🔐 Authentication System

### How Authentication Works

The BrandGPT API supports **dual authentication** for different use cases:

#### **Option 1: JWT Tokens (Web Applications)**
1. **User Registration**: Create account with username, email, password
2. **Login**: Exchange credentials for JWT access token
3. **Token Usage**: Include token in `Authorization: Bearer <jwt_token>` header
4. **Best For**: Web applications, interactive sessions

#### **Option 2: API Keys (Server-to-Server)**
1. **User Registration**: Create account (one-time setup)
2. **Generate API Key**: Use JWT to generate persistent API key
3. **Key Usage**: Include key in `Authorization: Bearer <api_key>` header  
4. **Best For**: Server integrations, automation, v1 API compatibility

Both methods provide:
- **User Isolation**: All content is automatically scoped to the authenticated user
- **Same Access**: Identical permissions and content access
- **Security**: Secure token validation and user identification

### Authentication Workflow

```mermaid
sequenceDiagram
    participant C as Client
    participant API as BrandGPT API
    participant DB as SQLite DB
    
    C->>API: POST /api/auth/register
    API->>DB: Create user record
    DB-->>API: User created
    API-->>C: 200 OK
    
    C->>API: POST /api/auth/token
    API->>DB: Validate credentials
    DB-->>API: User validated
    API-->>API: Generate JWT token
    API-->>C: JWT access token
    
    C->>API: Any protected endpoint
    Note over C,API: Authorization: Bearer <token>
    API-->>API: Validate JWT
    API-->>C: Access granted
```

## 🌐 Complete API Reference

### 🔐 Authentication Endpoints

#### Register User
Creates a new user account in the system.

**Endpoint:** `POST /api/auth/register`

**Request Body:**
```json
{
  "username": "john_doe",
  "email": "john@example.com", 
  "password": "secure_password123"
}
```

**Response:** `200 OK`
```json
{
  "id": 1,
  "username": "john_doe",
  "email": "john@example.com",
  "is_active": true,
  "created_at": "2024-01-15T10:30:00"
}
```

**Python Example:**
```python
import requests

response = requests.post(
    "http://localhost:9700/api/auth/register",
    json={
        "username": "john_doe",
        "email": "john@example.com",
        "password": "secure_password123"
    }
)
user = response.json()
print(f"User created: {user['username']} (ID: {user['id']})")
```

**JavaScript Example:**
```javascript
const response = await fetch('http://localhost:9700/api/auth/register', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        username: 'john_doe',
        email: 'john@example.com',
        password: 'secure_password123'
    })
});

const user = await response.json();
console.log(`User created: ${user.username} (ID: ${user.id})`);
```

**Error Responses:**
- `400 Bad Request`: Username or email already exists
- `422 Unprocessable Entity`: Invalid input format

#### Login / Get Access Token
Authenticates user and returns JWT access token for API access.

**Endpoint:** `POST /api/auth/token`

**Request Body:** (Form-encoded)
```
username=john_doe&password=secure_password123
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Python Example:**
```python
import requests

response = requests.post(
    "http://localhost:9700/api/auth/token",
    data={
        "username": "john_doe",
        "password": "secure_password123"
    },
    headers={"Content-Type": "application/x-www-form-urlencoded"}
)

token_data = response.json()
access_token = token_data["access_token"]

# Use token for subsequent requests
headers = {"Authorization": f"Bearer {access_token}"}
```

#### Generate API Key
Generate a persistent API key for server-to-server authentication (v1 compatibility).

**Endpoint:** `POST /api/auth/api-key`

**Authentication:** Required (JWT)

**Response:** `200 OK`
```json
{
  "api_key": "bgpt_2m3SQzl-WxbcGdW8N9P4rT6vY8zA1B3cD5e",
  "message": "API key generated successfully. Store it securely - it won't be shown again."
}
```

**Python Example:**
```python
# Generate API key using JWT token
response = requests.post(
    "http://localhost:9700/api/auth/api-key",
    headers={"Authorization": f"Bearer {jwt_token}"}
)

api_key_data = response.json()
api_key = api_key_data["api_key"]  # Save this securely!

# Use API key for all future requests (v1-style)
headers = {"Authorization": f"Bearer {api_key}"}
# Or without Bearer prefix:
headers = {"Authorization": api_key}
```

**JavaScript Example:**
```javascript
const response = await fetch('http://localhost:9700/api/auth/token', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: new URLSearchParams({
        username: 'john_doe',
        password: 'secure_password123'
    })
});

const tokenData = await response.json();
const accessToken = tokenData.access_token;

// Use token for subsequent requests
const headers = {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json'
};
```

**Error Responses:**
- `401 Unauthorized`: Invalid username or password

---

### 📋 Session Management

Sessions are containers for your conversations and document access. Each session can have its own AI persona (system prompt) while accessing all your ingested documents.

#### Create Session
Creates a new conversation session with optional AI persona.

**Endpoint:** `POST /api/sessions`

**Authentication:** Required (`Authorization: Bearer <token>`)

**Request Body Options:**

**Option 1: Using Stored Prompt**
```json
{
  "prompt_id": 123
}
```

**Option 2: Using Inline System Prompt**
```json
{
  "system_prompt": "You are a helpful business analyst. Focus on ROI and strategic insights."
}
```

**Option 3: Default Session (No Custom Prompt)**
```json
{}
```

**Response:** `200 OK`
```json
{
  "id": "abc123-def456-ghi789",
  "user_id": 1,
  "prompt_id": 123,
  "system_prompt": "You are a helpful business analyst...",
  "created_at": "2024-01-15T10:30:00"
}
```

**Python Example:**
```python
# Create session with stored prompt
session_response = requests.post(
    "http://localhost:9700/api/sessions",
    json={"prompt_id": 123},
    headers=headers
)

session_id = session_response.json()["id"]
print(f"Session created: {session_id}")

# Create session with inline prompt
session_response = requests.post(
    "http://localhost:9700/api/sessions",
    json={
        "system_prompt": "You are a technical expert. Focus on implementation details and best practices."
    },
    headers=headers
)
```

**JavaScript Example:**
```javascript
// Create session with stored prompt
const sessionResponse = await fetch('http://localhost:9700/api/sessions', {
    method: 'POST',
    headers: headers,
    body: JSON.stringify({
        prompt_id: 123
    })
});

const session = await sessionResponse.json();
console.log(`Session created: ${session.id}`);
```

#### List Sessions
Retrieves all sessions for the authenticated user.

**Endpoint:** `GET /api/sessions`

**Authentication:** Required

**Response:** `200 OK`
```json
[
  {
    "id": "abc123-def456-ghi789",
    "user_id": 1,
    "prompt_id": 123,
    "system_prompt": null,
    "created_at": "2024-01-15T10:30:00"
  },
  {
    "id": "xyz789-uvw456-rst123",
    "user_id": 1,
    "prompt_id": null,
    "system_prompt": "You are a creative writer...",
    "created_at": "2024-01-15T11:45:00"
  }
]
```

#### Get Session Details
Retrieve details for a specific session.

**Endpoint:** `GET /api/sessions/{session_id}`

**Authentication:** Required

**Response:** `200 OK`
```json
{
  "id": "abc123-def456-ghi789",
  "user_id": 1,
  "prompt_id": 123,
  "system_prompt": null,
  "created_at": "2024-01-15T10:30:00"
}
```

**Error Responses:**
- `404 Not Found`: Session not found or doesn't belong to user

#### Update Session
Change the AI persona for an existing session without losing conversation history.

**Endpoint:** `PATCH /api/sessions/{session_id}`

**Authentication:** Required

**Request Body:**
```json
{
  "prompt_id": 456,
  "system_prompt": "You are a data analyst focused on insights..."
}
```

**Parameters:**
- `prompt_id` (int, optional): ID of stored prompt to use
- `system_prompt` (string, optional): Custom system prompt text
- Set both to `null` to use default prompt

**Response:** `200 OK`
```json
{
  "id": "abc123-def456-ghi789",
  "user_id": 1,
  "prompt_id": 456,
  "system_prompt": null,
  "created_at": "2024-01-15T10:30:00"
}
```

**Python Example:**
```python
# Switch to a different persona mid-session
update_data = {"prompt_id": 456}
response = requests.patch(
    f"http://localhost:9700/api/sessions/{session_id}",
    json=update_data,
    headers=headers
)

print(f"Session prompt updated to ID: {response.json()['prompt_id']}")

# Use custom inline prompt
response = requests.patch(
    f"http://localhost:9700/api/sessions/{session_id}",
    json={"system_prompt": "You are a creative storyteller..."},
    headers=headers
)
```

**JavaScript Example:**
```javascript
// Switch session to different AI persona
const updateResponse = await fetch(`http://localhost:9700/api/sessions/${sessionId}`, {
    method: 'PATCH',
    headers: headers,
    body: JSON.stringify({ prompt_id: 456 })
});

const updatedSession = await updateResponse.json();
console.log(`Session updated: ${updatedSession.id}`);
```

#### Delete Session
Delete a session and all associated temporary documents (documents without group_id).

**Endpoint:** `DELETE /api/sessions/{session_id}`

**Authentication:** Required

**Response:** `200 OK`
```json
{
  "message": "Session deleted successfully"
}
```

**Important Notes:**
- Deletes all conversation messages in the session
- Deletes temporary documents (without group_id)
- **Preserves** persistent documents (with group_id) for reuse
- Cannot be undone

**Python Example:**
```python
response = requests.delete(
    f"http://localhost:9700/api/sessions/{session_id}",
    headers=headers
)
print(response.json()["message"])
```

#### Get Chat History
Retrieve all conversation messages for a session.

**Endpoint:** `GET /api/sessions/{session_id}/messages`

**Authentication:** Required

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "session_id": "abc123-def456-ghi789",
    "user_id": 1,
    "role": "user",
    "content": "What are the key insights from the business report?",
    "created_at": "2024-01-15T10:35:00"
  },
  {
    "id": 2,
    "session_id": "abc123-def456-ghi789",
    "user_id": 1,
    "role": "assistant",
    "content": "Based on the business report, there are three key insights:\n1. Revenue growth of 25% YoY\n2. Market expansion opportunities in Asia\n3. Digital transformation initiatives showing strong ROI",
    "created_at": "2024-01-15T10:35:15"
  },
  {
    "id": 3,
    "session_id": "abc123-def456-ghi789",
    "user_id": 1,
    "role": "user",
    "content": "Tell me more about the Asia expansion",
    "created_at": "2024-01-15T10:36:00"
  }
]
```

**Python Example:**
```python
# Get full conversation history
response = requests.get(
    f"http://localhost:9700/api/sessions/{session_id}/messages",
    headers=headers
)

messages = response.json()
print(f"Conversation has {len(messages)} messages:\n")

for msg in messages:
    role = "User" if msg["role"] == "user" else "AI"
    print(f"{role}: {msg['content'][:100]}...")
    print(f"  (Timestamp: {msg['created_at']})\n")
```

**JavaScript Example:**
```javascript
// Retrieve chat history
const response = await fetch(`http://localhost:9700/api/sessions/${sessionId}/messages`, {
    headers: headers
});

const messages = await response.json();
console.log(`Conversation history (${messages.length} messages):`);

messages.forEach(msg => {
    const role = msg.role === 'user' ? 'User' : 'AI';
    console.log(`${role}: ${msg.content.substring(0, 100)}...`);
});
```

---

### 🎭 AI Persona & Prompt Management

The prompt system allows you to create reusable AI personas with consistent behavior across sessions.

#### Create Prompt
Stores a reusable system prompt (AI persona) for use in sessions.

**Endpoint:** `POST /api/prompts`

**Authentication:** Required

**Request Body:**
```json
{
  "name": "Business Consultant",
  "description": "AI persona focused on business strategy and ROI analysis",
  "content": "You are an experienced business consultant with 15+ years in strategy consulting. Focus on business impact, ROI, market positioning, and strategic recommendations. Use business terminology and provide actionable insights. Always consider competitive advantages and market opportunities."
}
```

**Response:** `200 OK`
```json
{
  "id": 123,
  "name": "Business Consultant",
  "description": "AI persona focused on business strategy and ROI analysis",
  "content": "You are an experienced business consultant...",
  "created_by": 1,
  "created_at": "2024-01-15T10:30:00"
}
```

**Python Example:**
```python
# Create reusable AI personas
personas = [
    {
        "name": "Technical Expert",
        "description": "Senior software engineer focused on best practices",
        "content": "You are a senior software engineer with expertise in system architecture. Focus on technical implementation, performance optimization, scalability, and coding best practices. Provide detailed technical explanations with code examples when relevant."
    },
    {
        "name": "Creative Writer",
        "description": "Storyteller who makes content engaging and accessible",
        "content": "You are a creative writer and storyteller. Transform technical information into engaging narratives with human interest angles, analogies, and vivid descriptions. Make complex topics accessible through storytelling techniques."
    }
]

created_prompts = []
for persona in personas:
    response = requests.post(
        "http://localhost:9700/api/prompts",
        json=persona,
        headers=headers
    )
    created_prompts.append(response.json())
    print(f"Created persona: {persona['name']}")
```

**JavaScript Example:**
```javascript
const persona = {
    name: "Data Scientist",
    description: "Expert in statistical analysis and machine learning",
    content: "You are a data scientist with expertise in statistical analysis, machine learning, and data visualization. Focus on data patterns, statistical significance, predictive insights, and data-driven recommendations. Use quantitative reasoning and mention relevant metrics."
};

const response = await fetch('http://localhost:9700/api/prompts', {
    method: 'POST',
    headers: headers,
    body: JSON.stringify(persona)
});

const prompt = await response.json();
console.log(`Created persona: ${prompt.name} (ID: ${prompt.id})`);
```

#### List Prompts
Retrieves all stored prompts (AI personas) accessible to the user.

**Endpoint:** `GET /api/prompts`

**Authentication:** Required

**Response:** `200 OK`
```json
[
  {
    "id": 123,
    "name": "Business Consultant",
    "description": "AI persona focused on business strategy and ROI analysis",
    "content": "You are an experienced business consultant...",
    "created_by": 1,
    "created_at": "2024-01-15T10:30:00"
  },
  {
    "id": 124,
    "name": "Technical Expert",
    "description": "Senior software engineer focused on best practices",
    "content": "You are a senior software engineer...",
    "created_by": 1,
    "created_at": "2024-01-15T10:35:00"
  }
]
```

#### Get Prompt Details
Retrieve details for a specific AI persona prompt.

**Endpoint:** `GET /api/prompts/{prompt_id}`

**Authentication:** Required

**Response:** `200 OK`
```json
{
  "id": 123,
  "name": "Business Consultant",
  "description": "AI persona focused on business strategy and ROI analysis",
  "content": "You are an experienced business consultant with 15+ years in strategy consulting...",
  "created_by": 1,
  "created_at": "2024-01-15T10:30:00"
}
```

**Error Responses:**
- `404 Not Found`: Prompt not found

#### Update Prompt
Modify an existing AI persona. Only the creator can update their prompts.

**Endpoint:** `PUT /api/prompts/{prompt_id}`

**Authentication:** Required

**Request Body:**
```json
{
  "name": "Senior Business Consultant",
  "description": "Updated description with more focus on digital transformation",
  "content": "You are a senior business consultant specializing in digital transformation..."
}
```

**Parameters:** (All optional - only provided fields will be updated)
- `name` (string): Updated name for the prompt
- `description` (string): Updated description
- `content` (string): Updated system prompt content

**Response:** `200 OK`
```json
{
  "id": 123,
  "name": "Senior Business Consultant",
  "description": "Updated description with more focus on digital transformation",
  "content": "You are a senior business consultant specializing in digital transformation...",
  "created_by": 1,
  "created_at": "2024-01-15T10:30:00"
}
```

**Python Example:**
```python
# Update only specific fields
update_data = {
    "description": "Enhanced AI persona for strategic business analysis",
    "content": "You are a strategic business consultant with expertise in digital transformation, market analysis, and ROI optimization. Focus on actionable insights and measurable business outcomes."
}

response = requests.put(
    f"http://localhost:9700/api/prompts/{prompt_id}",
    json=update_data,
    headers=headers
)

updated_prompt = response.json()
print(f"Prompt updated: {updated_prompt['name']}")
```

**JavaScript Example:**
```javascript
const updateData = {
    name: "Senior Technical Architect",
    content: "You are a senior technical architect with deep expertise in distributed systems..."
};

const response = await fetch(`http://localhost:9700/api/prompts/${promptId}`, {
    method: 'PUT',
    headers: headers,
    body: JSON.stringify(updateData)
});

const updatedPrompt = await response.json();
console.log(`Prompt updated: ${updatedPrompt.name}`);
```

**Error Responses:**
- `403 Forbidden`: You can only update your own prompts
- `404 Not Found`: Prompt not found

#### Delete Prompt
Delete an AI persona prompt. Only the creator can delete their prompts.

**Endpoint:** `DELETE /api/prompts/{prompt_id}`

**Authentication:** Required

**Response:** `200 OK`
```json
{
  "message": "Prompt deleted successfully"
}
```

**Safety Features:**
- Only the creator can delete their prompts
- Warns if prompt is currently used by any sessions
- Cannot be undone

**Python Example:**
```python
response = requests.delete(
    f"http://localhost:9700/api/prompts/{prompt_id}",
    headers=headers
)

print(response.json()["message"])
```

**JavaScript Example:**
```javascript
const response = await fetch(`http://localhost:9700/api/prompts/${promptId}`, {
    method: 'DELETE',
    headers: headers
});

const result = await response.json();
console.log(result.message);
```

**Error Responses:**
- `403 Forbidden`: You can only delete your own prompts
- `404 Not Found`: Prompt not found

---

## 📚 Document Ingestion

The ingestion system processes multiple document formats and stores them as searchable vector embeddings. **All content is automatically scoped to your user account** - you can only search your own documents.

### How User-Scoped Content Works

```mermaid
graph LR
    A[User 1 Documents] --> B[User 1 Embeddings]
    C[User 2 Documents] --> D[User 2 Embeddings]
    E[User 3 Documents] --> F[User 3 Embeddings]

    B --> G[Qdrant Vector DB]
    D --> G
    F --> G

    G --> H{Query with User Filter}
    H --> I[Only User's Results]

    style B fill:#e3f2fd
    style D fill:#fff3e0
    style F fill:#e8f5e8
    style I fill:#fce4ec
```

**Key Concepts:**
- **Privacy**: Your documents are never visible to other users
- **Persistence**: Documents remain available across all your sessions
- **Searchability**: All your content is searchable from any session
- **Scalability**: Add unlimited documents without performance degradation

### Document Lifecycle Patterns

BrandGPT supports two document lifecycle patterns to fit different use cases:

**1. Persistent Documents (with `group_id`)**
- Documents tagged with a `group_id` are persistent across sessions
- Survive session deletion and remain available indefinitely
- Ideal for: Knowledge bases, reference materials, company documents
- Example: Product catalogs, technical documentation, research papers

**2. Temporary Documents (without `group_id`)**
- Documents without a `group_id` are scoped to a specific session
- Automatically deleted when the session is deleted
- Ideal for: Temporary analysis, one-time uploads, experimental data
- Example: Draft documents, temporary notes, test data

**Usage Example:**
```python
# Persistent document - survives session deletion
persistent_data = {
    "data": {"product": "Widget", "price": 99.99},
    "group_id": "product_catalog",  # Makes it persistent
    "session_id": session_id
}

# Temporary document - deleted with session
temporary_data = {
    "data": {"draft": "analysis notes..."},
    "session_id": session_id  # No group_id = temporary
}
```

**Session Deletion Behavior:**
```mermaid
graph TD
    A[Delete Session] --> B{Check Documents}
    B -->|Has group_id| C[Keep Document]
    B -->|No group_id| D[Delete Document]
    C --> E[Document Available in Future Sessions]
    D --> F[Document Removed from Vector DB]

    style C fill:#c8e6c9
    style D fill:#ffcdd2
    style E fill:#a5d6a7
    style F fill:#ef9a9a
```

### File Upload (PDF, Text, JSON)
Processes and stores uploaded files with automatic format detection. **Asynchronous processing** - returns immediately while file is processed in background.

**Endpoint:** `POST /api/ingest/file`

**Authentication:** Required

**Request:** Multipart form data with file upload

**Form Parameters:**
- `file` (required): The file to upload
- `session_id` (optional): Session ID to associate with the document
- `group_id` (optional): Group ID for persistent document organization

**Python Example:**
```python
import time

# Upload PDF document with session_id
session_id = "abc123-def456-ghi789"
with open("business_report.pdf", "rb") as file:
    files = {"file": ("business_report.pdf", file, "application/pdf")}
    data = {"session_id": session_id}
    response = requests.post(
        "http://localhost:9700/api/ingest/file",
        files=files,
        data=data,
        headers={"Authorization": f"Bearer {access_token}"}  # Note: no Content-Type for multipart
    )

# Returns immediately with 202 Accepted
result = response.json()
document_id = result['document_id']
print(f"Document ingestion queued: {document_id}")

# Poll for completion status
while True:
    status_response = requests.get(
        f"http://localhost:9700/api/document/{document_id}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    doc_status = status_response.json()

    if doc_status['processed'] == 'completed':
        print("✅ Document processing completed!")
        break
    elif doc_status['processed'] == 'failed':
        print(f"❌ Processing failed: {doc_status['error_message']}")
        break

    print(f"⏳ Status: {doc_status['processed']}...")
    time.sleep(3)  # Poll every 3 seconds

# Upload with group_id for persistent storage
with open("company_data.json", "rb") as file:
    files = {"file": ("company_data.json", file, "application/json")}
    data = {
        "session_id": session_id,
        "group_id": "company_docs_2024"  # Makes it persistent
    }
    response = requests.post(
        "http://localhost:9700/api/ingest/file",
        files=files,
        data=data,
        headers={"Authorization": f"Bearer {access_token}"}
    )
```

**JavaScript Example:**
```javascript
// Upload PDF using FormData
const sessionId = 'abc123-def456-ghi789';
const fileInput = document.getElementById('fileInput'); // HTML file input
const file = fileInput.files[0];

const formData = new FormData();
formData.append('file', file);
formData.append('session_id', sessionId);
formData.append('group_id', 'company_docs_2024');  // Optional: for persistent storage

const response = await fetch('http://localhost:9700/api/ingest/file', {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${accessToken}`
        // Note: Don't set Content-Type for FormData, browser sets it automatically
    },
    body: formData
});

// Response comes back immediately with 202 Accepted
const result = await response.json();
const documentId = result.document_id;
console.log(`Document ingestion queued: ${documentId}`);

// Poll for status until complete
const pollInterval = setInterval(async () => {
    const statusResponse = await fetch(`http://localhost:9700/api/document/${documentId}`, {
        headers: { 'Authorization': `Bearer ${accessToken}` }
    });

    const docStatus = await statusResponse.json();

    if (docStatus.processed === 'completed') {
        clearInterval(pollInterval);
        console.log('✅ Document processing completed!');
    } else if (docStatus.processed === 'failed') {
        clearInterval(pollInterval);
        console.error(`❌ Processing failed: ${docStatus.error_message}`);
    } else {
        console.log(`⏳ Status: ${docStatus.processed}...`);
    }
}, 3000);  // Poll every 3 seconds
```

**Response:** `202 Accepted` (immediate return)
```json
{
  "document_id": 456,
  "status": "queued",
  "message": "File ingestion queued for processing"
}
```

**Status Values:**
- `queued`: Document is waiting to be processed
- `processing`: Document is currently being processed
- `completed`: Processing finished successfully
- `failed`: Processing encountered an error

**Supported File Types:**
- **PDF**: Extracts text, preserves structure, handles tables
- **Text**: Direct processing with automatic chunking
- **JSON**: Smart conversion to natural language format
- **Auto-detection**: System automatically detects JSON in .txt files

### URL Ingestion
Crawls and processes web content with configurable depth for comprehensive knowledge base creation. **Asynchronous processing** - returns immediately while URL is scraped and processed in background.

**Endpoint:** `POST /api/ingest/url`

**Authentication:** Required

**Request Body:**
```json
{
  "session_id": "abc123-def456-ghi789",
  "content_type": "url",
  "url": "https://example.com/article",
  "max_depth": 2,
  "group_id": "company_docs"
}
```

**Parameters:**
- `url` (required): The URL to scrape
- `session_id` (optional): Session ID to associate with the document
- `group_id` (optional): Group ID for persistent document organization
- `content_type` (optional): Must be "url" if provided
- `max_depth` (optional): Crawl depth (default: 1)

**Depth Parameter Explanation:**
- `max_depth: 1` - Only scrapes the provided URL (default)
- `max_depth: 2` - Scrapes the URL + all pages it links to (1 level deep)
- `max_depth: 3` - Scrapes the URL + linked pages + their linked pages (2 levels deep)
- Maximum allowed depth: 10 (configurable via `MAX_SCRAPE_DEPTH` environment variable)

**Response:** `202 Accepted` (immediate return)
```json
{
  "document_id": 789,
  "status": "queued",
  "message": "URL ingestion queued for processing"
}
```

**Python Example:**
```python
import time

# Crawl single page with progress tracking
url_data = {
    "session_id": session_id,
    "content_type": "url",
    "url": "https://en.wikipedia.org/wiki/Artificial_intelligence",
    "max_depth": 1  # Just the main page
}

response = requests.post(
    "http://localhost:9700/api/ingest/url",
    json=url_data,
    headers=headers
)

# Returns immediately with 202 Accepted
result = response.json()
document_id = result['document_id']
print(f"URL crawling queued: {document_id}")

# Poll for completion with progress tracking
while True:
    status_response = requests.get(
        f"http://localhost:9700/api/document/{document_id}",
        headers=headers
    )
    doc_status = status_response.json()

    # Check completion status
    if doc_status['processed'] == 'completed':
        print("✅ URL processing completed!")
        break
    elif doc_status['processed'] == 'failed':
        print(f"❌ Processing failed: {doc_status['error_message']}")
        break

    # Show progress details
    metadata = doc_status.get('doc_metadata', {})
    phase = metadata.get('phase', 'unknown')
    progress = metadata.get('progress_percent', 0)
    print(f"⏳ Phase: {phase}, Progress: {progress}%")

    time.sleep(3)  # Poll every 3 seconds

# Crawl website with depth - comprehensive knowledge base creation
deep_crawl = {
    "session_id": session_id,
    "content_type": "url",
    "url": "https://company.com/docs/",
    "max_depth": 3,  # Scrapes: main page + all linked pages + their linked pages
    "group_id": "company_docs"  # Makes it persistent
}

response = requests.post(
    "http://localhost:9700/api/ingest/url",
    json=deep_crawl,
    headers=headers
)
```

**JavaScript Example:**
```javascript
const urlData = {
    session_id: sessionId,
    content_type: 'url',
    url: 'https://docs.company.com/getting-started',
    max_depth: 2
};

const response = await fetch('http://localhost:9700/api/ingest/url', {
    method: 'POST',
    headers: headers,
    body: JSON.stringify(urlData)
});

// Response comes back immediately with 202 Accepted
const result = await response.json();
const documentId = result.document_id;
console.log(`URL crawling queued: ${documentId}`);

// Poll for status with progress tracking
const pollInterval = setInterval(async () => {
    const statusResponse = await fetch(`http://localhost:9700/api/document/${documentId}`, {
        headers: headers
    });

    const docStatus = await statusResponse.json();

    if (docStatus.processed === 'completed') {
        clearInterval(pollInterval);
        console.log('✅ URL processing completed!');
    } else if (docStatus.processed === 'failed') {
        clearInterval(pollInterval);
        console.error(`❌ Processing failed: ${docStatus.error_message}`);
    } else {
        // Show progress
        const metadata = docStatus.doc_metadata || {};
        const phase = metadata.phase || 'unknown';
        const progress = metadata.progress_percent || 0;
        console.log(`⏳ Phase: ${phase}, Progress: ${progress}%`);
    }
}, 3000);  // Poll every 3 seconds
```

**Processing Phases:**
- `scraping`: Downloading and extracting content from URL
- `embedding`: Generating vector embeddings for search
- `completed`: Processing finished successfully
- `failed`: An error occurred during processing

**URL Processing Features:**
- **Asynchronous Processing**: Immediate response, no timeout issues
- **Progress Tracking**: Real-time phase and percentage updates
- **Smart Content Extraction**: Removes navigation, ads, and boilerplate content
- **Same-Domain Restriction**: Only follows links within the same domain for security
- **Multi-Page Processing**: Each discovered page becomes a separate searchable document
- **Configurable Depth Crawling**: Control how many levels of links to follow (1-10 levels)
- **Rate Limiting**: Implements delays between requests (configurable via `DOWNLOAD_DELAY`)
- **Link Limitation**: Configurable maximum links per page (default: 20) to prevent excessive crawling

### Structured Data Ingestion
Ingest JSON objects/arrays while preserving original structure for RAG (v1 API compatibility). **Asynchronous processing** - returns immediately while data is processed in background.

**Endpoint:** `POST /api/ingest/structured`

**Authentication:** Required

**Request Body:**
```json
{
  "data": {
    "id": 1,
    "name": "Product A",
    "price": 99.99,
    "features": ["wireless", "noise-cancelling"]
  },
  "group_id": "products_2024",
  "session_id": "abc123-def456-ghi789",
  "metadata": {
    "source": "product_catalog",
    "version": "2024.1"
  }
}
```

**For Arrays:**
```json
{
  "data": [
    {"id": 1, "name": "Product A", "price": 99.99},
    {"id": 2, "name": "Product B", "price": 149.99}
  ],
  "group_id": "products_2024"
}
```

**Response:** `202 Accepted` (immediate return)
```json
{
  "document_id": 456,
  "status": "queued",
  "items_processed": 2,
  "message": "Structured data ingestion queued for processing"
}
```

**Python Example:**
```python
import time

# Single object ingestion
structured_data = {
    "data": {
        "company": "TechCorp",
        "departments": [
            {"name": "Engineering", "employees": 50},
            {"name": "Sales", "employees": 30}
        ]
    },
    "group_id": "company_data",
    "session_id": session_id,
    "metadata": {"source": "hr_system"}
}

response = requests.post(
    "http://localhost:9700/api/ingest/structured",
    json=structured_data,
    headers=headers
)

# Returns immediately with 202 Accepted
result = response.json()
document_id = result['document_id']
print(f"Structured data ingestion queued: {document_id}")

# Poll for completion
while True:
    status_response = requests.get(
        f"http://localhost:9700/api/document/{document_id}",
        headers=headers
    )
    doc_status = status_response.json()

    if doc_status['processed'] == 'completed':
        print("✅ Data processing completed!")
        break
    elif doc_status['processed'] == 'failed':
        print(f"❌ Processing failed: {doc_status['error_message']}")
        break

    print(f"⏳ Status: {doc_status['processed']}...")
    time.sleep(3)

# Array of objects (v1-style)
products_data = {
    "data": [
        {"id": 1, "name": "Laptop", "price": 999},
        {"id": 2, "name": "Mouse", "price": 29}
    ],
    "group_id": "inventory_2024"
}

response = requests.post(
    "http://localhost:9700/api/ingest/structured",
    json=products_data,
    headers=headers
)
```

**JavaScript Example:**
```javascript
const structuredData = {
    data: {
        project: "Website Redesign",
        tasks: [
            {name: "UI Design", status: "completed"},
            {name: "Backend API", status: "in_progress"}
        ]
    },
    group_id: "projects_2024",
    session_id: sessionId
};

const response = await fetch('http://localhost:9700/api/ingest/structured', {
    method: 'POST',
    headers: headers,
    body: JSON.stringify(structuredData)
});

// Response comes back immediately with 202 Accepted
const result = await response.json();
const documentId = result.document_id;
console.log(`Structured data ingestion queued: ${documentId}`);

// Poll for status
const pollInterval = setInterval(async () => {
    const statusResponse = await fetch(`http://localhost:9700/api/document/${documentId}`, {
        headers: headers
    });

    const docStatus = await statusResponse.json();

    if (docStatus.processed === 'completed') {
        clearInterval(pollInterval);
        console.log('✅ Data processing completed!');
    } else if (docStatus.processed === 'failed') {
        clearInterval(pollInterval);
        console.error(`❌ Processing failed: ${docStatus.error_message}`);
    }
}, 3000);
```

**Structured Data Features:**
- **Asynchronous Processing**: Immediate response, no blocking operations
- **Original Structure Preserved**: JSON structure maintained for precise retrieval
- **Natural Language Conversion**: Automatically generates searchable text for RAG
- **Group Organization**: Content categorization via group_id (v1 compatibility)
- **Flexible Input**: Supports single objects or arrays of objects
- **Progress Tracking**: Poll status to monitor processing completion

### Check Document Status
Monitor the processing status of ingested documents with detailed progress tracking.

#### Get Single Document Status (New)

**Endpoint:** `GET /api/document/{document_id}`

**Authentication:** Required

**Use Case:** Poll this endpoint after receiving a `document_id` from an ingestion endpoint to track processing progress.

**Response:** `200 OK`
```json
{
  "id": 789,
  "user_id": 1,
  "session_id": "abc123-def456-ghi789",
  "group_id": "company_docs",
  "url": "https://example.com/article",
  "content_type": "url",
  "processed": "processing",
  "created_at": "2024-01-15T10:30:00",
  "started_at": "2024-01-15T10:30:01",
  "processed_at": null,
  "error_message": null,
  "doc_metadata": {
    "phase": "embedding",
    "progress_percent": 45,
    "chunks_total": 14,
    "chunks_processed": 7
  }
}
```

**Status Values:**
- `queued`: Document is waiting to be processed
- `processing`: Document is currently being processed
- `completed`: Processing finished successfully
- `failed`: Processing encountered an error

**Processing Phases (in `doc_metadata`):**
- `scraping`: Downloading and extracting content (URLs only)
- `embedding`: Generating vector embeddings for search
- `completed`: All processing steps finished
- `failed`: An error occurred

**Python Example:**
```python
import time

# After uploading/ingesting, poll for status
document_id = 789

while True:
    response = requests.get(
        f"http://localhost:9700/api/document/{document_id}",
        headers=headers
    )
    doc = response.json()

    print(f"Status: {doc['processed']}")

    if doc['processed'] == 'completed':
        print(f"✅ Completed at {doc['processed_at']}")
        break
    elif doc['processed'] == 'failed':
        print(f"❌ Failed: {doc['error_message']}")
        break
    elif doc['processed'] == 'processing':
        # Show detailed progress
        metadata = doc.get('doc_metadata', {})
        phase = metadata.get('phase', 'unknown')
        progress = metadata.get('progress_percent', 0)
        print(f"⏳ Phase: {phase}, Progress: {progress}%")

    time.sleep(3)  # Poll every 3 seconds
```

**JavaScript Example:**
```javascript
const documentId = 789;

const pollStatus = setInterval(async () => {
    const response = await fetch(`http://localhost:9700/api/document/${documentId}`, {
        headers: headers
    });

    const doc = await response.json();

    if (doc.processed === 'completed') {
        clearInterval(pollStatus);
        console.log(`✅ Completed at ${doc.processed_at}`);
    } else if (doc.processed === 'failed') {
        clearInterval(pollStatus);
        console.error(`❌ Failed: ${doc.error_message}`);
    } else if (doc.processed === 'processing') {
        const metadata = doc.doc_metadata || {};
        const phase = metadata.phase || 'unknown';
        const progress = metadata.progress_percent || 0;
        console.log(`⏳ Phase: ${phase}, Progress: ${progress}%`);
    }
}, 3000);
```

#### List Session Documents

**Endpoint:** `GET /api/documents/{session_id}`

**Authentication:** Required

**Use Case:** Get all documents associated with a session.

**Response:** `200 OK`
```json
[
  {
    "id": 456,
    "session_id": "abc123-def456-ghi789",
    "filename": "business_report.pdf",
    "content_type": "pdf",
    "processed": "completed",
    "created_at": "2024-01-15T10:30:00",
    "started_at": "2024-01-15T10:30:01",
    "processed_at": "2024-01-15T10:35:00",
    "error_message": null,
    "doc_metadata": {
      "phase": "completed",
      "progress_percent": 100
    }
  },
  {
    "id": 789,
    "session_id": "abc123-def456-ghi789",
    "url": "https://example.com/article",
    "content_type": "url",
    "processed": "processing",
    "created_at": "2024-01-15T10:35:00",
    "started_at": "2024-01-15T10:35:02",
    "processed_at": null,
    "error_message": null,
    "doc_metadata": {
      "phase": "embedding",
      "progress_percent": 60
    }
  }
]
```

### Delete Documents
Remove documents from your knowledge base with flexible deletion options.

**Endpoint:** `DELETE /api/data`

**Authentication:** Required

**Request Body (choose one deletion method):**

**Option 1: Delete by Group ID**
```json
{
  "group_id": "products_2024"
}
```

**Option 2: Delete by Session ID**
```json
{
  "session_id": "abc123-def456-ghi789"
}
```

**Option 3: Delete by Document ID**
```json
{
  "document_id": 456
}
```

**Response:** `200 OK`
```json
{
  "deleted_count": 3,
  "message": "Successfully deleted 3 documents"
}
```

**Python Example:**
```python
# Delete all documents in a group
delete_request = {"group_id": "test_data_2024"}
response = requests.delete(
    "http://localhost:9700/api/data",
    json=delete_request,
    headers=headers
)

result = response.json()
print(f"Deleted {result['deleted_count']} documents")

# Delete a specific document
response = requests.delete(
    "http://localhost:9700/api/data",
    json={"document_id": 456},
    headers=headers
)

# Delete all documents in a session
response = requests.delete(
    "http://localhost:9700/api/data",
    json={"session_id": session_id},
    headers=headers
)
```

**JavaScript Example:**
```javascript
// Delete documents by group
const deleteResponse = await fetch('http://localhost:9700/api/data', {
    method: 'DELETE',
    headers: headers,
    body: JSON.stringify({ group_id: 'test_data_2024' })
});

const result = await deleteResponse.json();
console.log(`Deleted ${result.deleted_count} documents`);
```

**Important Notes:**
- Deletion removes both database records and vector embeddings
- User isolation is enforced - you can only delete your own documents
- Deletion is permanent and cannot be undone
- At least one deletion criterion must be provided
- Only one criterion can be used per request

---

## 🔍 RAG Query System

The RAG (Retrieval-Augmented Generation) system searches your documents and generates contextual responses using advanced AI.

### How RAG Works

```mermaid
sequenceDiagram
    participant U as User
    participant API as BrandGPT API
    participant V as Vector DB
    participant R as Reranker
    participant L as Ollama LLM
    
    U->>API: POST /api/query
    Note over U,API: "What are the key insights from my documents?"
    
    API->>API: Extract user_id from JWT
    API->>V: Search vectors (filtered by user_id)
    V-->>API: Top 20 similar documents
    
    API->>R: Rerank by relevance
    R-->>API: Top 5 most relevant docs
    
    API->>API: Prepare context from docs
    API->>L: Generate response with context
    Note over API,L: System prompt + context + query
    L-->>API: Generated response
    
    API-->>U: Response + source documents
```

### Query Documents
Search your documents and get AI-generated responses with source attribution and conversation memory.

**Endpoint:** `POST /api/query`

**Authentication:** Required

**Request Body:**
```json
{
  "query": "What are the main business opportunities mentioned in the reports?",
  "session_id": "abc123-def456-ghi789",
  "use_system_prompt": true,
  "group_id": "business_reports_2024"
}
```

**Parameters:**
- `query` (string): Your question or search query
- `session_id` (string, optional): Session ID for conversation context and history
- `use_system_prompt` (boolean): Whether to use session's AI persona (default: true)
- `group_id` (string, optional): Filter results by group ID for content organization (v1 compatibility)

**Conversation Memory:**
When a `session_id` is provided, the system automatically:
- Retrieves the last 10 messages from the session for context
- Stores your current query as a user message
- Stores the AI response as an assistant message
- Uses conversation history to provide context-aware responses
- Enables natural multi-turn dialogues with follow-up questions

**Response:** `200 OK`
```json
{
  "response": "Based on the ingested documents, there are three main business opportunities identified:\n\n1. **Digital Transformation**: The reports highlight significant potential in modernizing legacy systems, with an estimated ROI of 300% over 18 months.\n\n2. **Market Expansion**: Analysis shows untapped markets in Southeast Asia, particularly in the fintech sector, representing a $2.5B opportunity.\n\n3. **AI Integration**: Implementation of AI-driven automation could reduce operational costs by 25-30% while improving customer satisfaction scores.",
  "sources": [
    {
      "text": "Digital transformation initiatives show strong ROI potential, with companies reporting average returns of 250-400% within the first two years...",
      "metadata": {
        "filename": "business_report.pdf",
        "page_number": 15,
        "document_id": 456
      }
    },
    {
      "text": "Southeast Asian markets present significant growth opportunities, particularly in financial technology sectors...",
      "metadata": {
        "url": "https://research.com/market-analysis",
        "document_id": 789
      }
    }
  ],
  "error": null
}
```

**Python Example:**
```python
# Query with specific session (uses session's AI persona)
query_data = {
    "query": "Summarize the key technical challenges mentioned in the documentation",
    "session_id": session_id,
    "use_system_prompt": True  # Use the session's AI persona
}

response = requests.post(
    "http://localhost:9700/api/query",
    json=query_data,
    headers=headers
)

result = response.json()
print("AI Response:")
print(result["response"])

print(f"\nBased on {len(result['sources'])} source documents:")
for i, source in enumerate(result["sources"], 1):
    metadata = source["metadata"]
    if "filename" in metadata:
        print(f"{i}. {metadata['filename']} (Page {metadata.get('page_number', '?')})")
    else:
        print(f"{i}. {metadata.get('url', 'Unknown source')}")

# Query without session-specific persona (default behavior)
general_query = {
    "query": "What is the overall sentiment of the content?",
    "use_system_prompt": False  # Use default AI behavior
}

response = requests.post(
    "http://localhost:9700/api/query",
    json=general_query,
    headers=headers
)

# Query specific group content (v1 compatibility)
group_query = {
    "query": "List all products and their prices",
    "group_id": "products_2024",  # Only search within this group
    "use_system_prompt": False
}

response = requests.post(
    "http://localhost:9700/api/query",
    json=group_query,
    headers=headers
)

# Query combining session persona with group filtering
persona_group_query = {
    "query": "Analyze the technical risks in this project",
    "session_id": session_id,
    "group_id": "project_alpha",
    "use_system_prompt": True  # Use AI persona + filter by group
}

response = requests.post(
    "http://localhost:9700/api/query",
    json=persona_group_query,
    headers=headers
)
```

**JavaScript Example:**
```javascript
// Query with AI persona
const queryData = {
    query: "What are the main risks identified in the analysis?",
    session_id: sessionId,
    use_system_prompt: true
};

const response = await fetch('http://localhost:9700/api/query', {
    method: 'POST',
    headers: headers,
    body: JSON.stringify(queryData)
});

const result = await response.json();

console.log("AI Response:", result.response);
console.log(`\nSources (${result.sources.length}):`);
result.sources.forEach((source, index) => {
    const metadata = source.metadata;
    const sourceInfo = metadata.filename || metadata.url || 'Unknown source';
    console.log(`${index + 1}. ${sourceInfo}`);
});
```

**RAG Pipeline Features:**
- **User-Scoped Search**: Only searches your documents, never other users' content
- **Semantic Search**: Finds relevant content even with different wording
- **Advanced Reranking**: Uses cross-encoder models to improve relevance
- **Source Attribution**: Always shows which documents contributed to the answer
- **Persona Consistency**: Maintains AI persona behavior across queries
- **Conversation Memory**: Remembers previous messages for context-aware responses
- **Multi-Turn Dialogues**: Natural follow-up questions that reference earlier context

### Multi-Turn Conversation Example

```python
# First query in a session
query1 = {
    "query": "What are the key insights from the business report?",
    "session_id": session_id,
    "use_system_prompt": True
}

response1 = requests.post("http://localhost:9700/api/query", json=query1, headers=headers)
print("AI:", response1.json()["response"])
# AI: "The report highlights three key insights: 1) Revenue growth of 25% YoY..."

# Follow-up question - AI remembers the previous context
query2 = {
    "query": "What's driving that revenue growth?",  # References "that" from previous answer
    "session_id": session_id,  # Same session = conversation memory
    "use_system_prompt": True
}

response2 = requests.post("http://localhost:9700/api/query", json=query2, headers=headers)
print("AI:", response2.json()["response"])
# AI: "The revenue growth is primarily driven by..." (understands context)

# Another follow-up
query3 = {
    "query": "How does this compare to our competitors?",
    "session_id": session_id,
    "use_system_prompt": True
}

response3 = requests.post("http://localhost:9700/api/query", json=query3, headers=headers)
# AI understands "this" refers to the revenue growth mentioned earlier
```

**Conversation Flow:**
```mermaid
sequenceDiagram
    participant User
    participant API
    participant DB as Message Storage
    participant LLM as Ollama LLM

    User->>API: Query 1: "What are the key insights?"
    API->>DB: Retrieve conversation history (0 messages)
    API->>LLM: Generate response with context
    LLM-->>API: Response
    API->>DB: Store user message + AI response
    API-->>User: Response

    User->>API: Query 2: "What's driving that growth?"
    API->>DB: Retrieve conversation history (2 messages)
    Note over API,LLM: AI now knows "that" refers to<br/>the growth mentioned in Query 1
    API->>LLM: Generate response with full context
    LLM-->>API: Context-aware response
    API->>DB: Store new messages
    API-->>User: Response

    User->>API: Query 3: "How does this compare?"
    API->>DB: Retrieve conversation history (4 messages)
    Note over API,LLM: Full conversation context enables<br/>natural dialogue
    API->>LLM: Generate response
    LLM-->>API: Response
    API->>DB: Store messages
    API-->>User: Response
```

---

## 💡 Usage Examples

### Complete Workflow Example

Here's a complete example showing how to use all the main features:

**Python Complete Example:**
```python
import requests
import time

class BrandGPTClient:
    def __init__(self, base_url="http://localhost:9700"):
        self.base_url = base_url
        self.session = requests.Session()
        self.token = None
    
    def register_and_login(self, username, email, password):
        """Register user and get access token"""
        # Register
        user_data = {
            "username": username,
            "email": email,
            "password": password
        }
        
        try:
            response = self.session.post(f"{self.base_url}/api/auth/register", json=user_data)
            if response.status_code == 400:
                print("User already exists, proceeding to login")
        except Exception as e:
            print(f"Registration failed: {e}")
        
        # Login
        login_data = {
            "username": username,
            "password": password
        }
        response = self.session.post(
            f"{self.base_url}/api/auth/token",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        token_data = response.json()
        self.token = token_data["access_token"]
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        print(f"✅ Logged in as {username}")
    
    def create_ai_persona(self, name, description, content):
        """Create a reusable AI persona"""
        persona_data = {
            "name": name,
            "description": description,
            "content": content
        }
        response = self.session.post(f"{self.base_url}/api/prompts", json=persona_data)
        persona = response.json()
        print(f"✅ Created AI persona: {name} (ID: {persona['id']})")
        return persona["id"]
    
    def create_session_with_persona(self, prompt_id):
        """Create a session with specific AI persona"""
        session_data = {"prompt_id": prompt_id}
        response = self.session.post(f"{self.base_url}/api/sessions", json=session_data)
        session = response.json()
        print(f"✅ Created session: {session['id']}")
        return session["id"]
    
    def upload_document(self, session_id, file_path, group_id=None):
        """Upload and process a document"""
        with open(file_path, 'rb') as file:
            files = {"file": (file_path, file)}
            data = {"session_id": session_id}
            if group_id:
                data["group_id"] = group_id
            response = self.session.post(
                f"{self.base_url}/api/ingest/file",
                files=files,
                data=data
            )

        result = response.json()
        print(f"✅ Document uploaded: {file_path} (Doc ID: {result['document_id']})")
        return result["document_id"]
    
    def crawl_website(self, session_id, url, max_depth=2):
        """Crawl and ingest website content"""
        url_data = {
            "session_id": session_id,
            "content_type": "url",
            "url": url,
            "max_depth": max_depth
        }
        response = self.session.post(f"{self.base_url}/api/ingest/url", json=url_data)
        result = response.json()
        print(f"✅ Website crawling started: {url} (Doc ID: {result['document_id']})")
        return result["document_id"]
    
    def wait_for_processing(self, session_id, timeout=60):
        """Wait for document processing to complete"""
        print("⏳ Waiting for document processing...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            response = self.session.get(f"{self.base_url}/api/documents/{session_id}")
            documents = response.json()
            
            processing_docs = [doc for doc in documents if doc.get("processed") == "processing"]
            if not processing_docs:
                print("✅ All documents processed")
                return True
            
            time.sleep(5)
        
        print("⚠️ Timeout waiting for processing")
        return False
    
    def query_documents(self, query, session_id=None, use_persona=True):
        """Query documents with AI response"""
        query_data = {
            "query": query,
            "use_system_prompt": use_persona
        }
        if session_id:
            query_data["session_id"] = session_id

        response = self.session.post(f"{self.base_url}/api/query", json=query_data)
        result = response.json()

        print(f"\n🤖 AI Response:")
        print(result["response"])
        print(f"\n📚 Based on {len(result['sources'])} sources:")
        for i, source in enumerate(result["sources"][:3], 1):
            metadata = source["metadata"]
            source_info = metadata.get("filename") or metadata.get("url", "Unknown")
            print(f"  {i}. {source_info}")

        return result

    def get_chat_history(self, session_id):
        """Retrieve conversation history"""
        response = self.session.get(f"{self.base_url}/api/sessions/{session_id}/messages")
        messages = response.json()

        print(f"\n💬 Conversation History ({len(messages)} messages):")
        for msg in messages:
            role = "👤 User" if msg["role"] == "user" else "🤖 AI"
            print(f"\n{role}:")
            print(f"  {msg['content'][:150]}...")

        return messages

# Complete workflow example
def main():
    client = BrandGPTClient()
    
    # 1. Authentication
    client.register_and_login(
        username="demo_user",
        email="demo@example.com", 
        password="secure_password123"
    )
    
    # 2. Create AI personas
    business_persona_id = client.create_ai_persona(
        name="Business Strategist",
        description="Expert in business strategy and market analysis", 
        content="You are a senior business strategist with 15+ years of experience. Focus on strategic insights, market opportunities, competitive analysis, and ROI. Provide actionable business recommendations."
    )
    
    technical_persona_id = client.create_ai_persona(
        name="Technical Architect",
        description="Senior software architect and technical leader",
        content="You are a senior technical architect. Focus on system design, scalability, performance, and technical best practices. Provide detailed technical analysis and implementation recommendations."
    )
    
    # 3. Create sessions with different personas
    business_session = client.create_session_with_persona(business_persona_id)
    technical_session = client.create_session_with_persona(technical_persona_id)
    
    # 4. Upload documents (you would have actual files)
    # client.upload_document(business_session, "business_plan.pdf")
    # client.upload_document(technical_session, "technical_specs.json") 
    
    # 5. Crawl relevant websites
    client.crawl_website(business_session, "https://en.wikipedia.org/wiki/Business_strategy", max_depth=1)
    client.crawl_website(technical_session, "https://en.wikipedia.org/wiki/Software_architecture", max_depth=1)
    
    # 6. Wait for processing
    client.wait_for_processing(business_session)
    client.wait_for_processing(technical_session)
    
    # 7. Query with different personas
    query = "What are the key principles and best practices mentioned in the content?"

    print("\n" + "="*60)
    print("BUSINESS STRATEGIST PERSPECTIVE:")
    print("="*60)
    client.query_documents(query, business_session, use_persona=True)

    print("\n" + "="*60)
    print("TECHNICAL ARCHITECT PERSPECTIVE:")
    print("="*60)
    client.query_documents(query, technical_session, use_persona=True)

    # 8. Multi-turn conversation with context
    print("\n" + "="*60)
    print("MULTI-TURN CONVERSATION DEMO:")
    print("="*60)

    # First question
    client.query_documents(
        "What is the main topic discussed?",
        business_session,
        use_persona=True
    )

    # Follow-up question (AI remembers context)
    client.query_documents(
        "Can you elaborate on that?",  # "that" refers to previous answer
        business_session,
        use_persona=True
    )

    # Another follow-up
    client.query_documents(
        "What are the practical implications?",
        business_session,
        use_persona=True
    )

    # 9. View conversation history
    client.get_chat_history(business_session)

if __name__ == "__main__":
    main()
```

**JavaScript Complete Example:**
```javascript
class BrandGPTClient {
    constructor(baseUrl = 'http://localhost:9700') {
        this.baseUrl = baseUrl;
        this.token = null;
    }
    
    async registerAndLogin(username, email, password) {
        // Register user
        try {
            await fetch(`${this.baseUrl}/api/auth/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, email, password })
            });
        } catch (error) {
            console.log('User might already exist, proceeding to login');
        }
        
        // Login and get token
        const response = await fetch(`${this.baseUrl}/api/auth/token`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: new URLSearchParams({ username, password })
        });
        
        const tokenData = await response.json();
        this.token = tokenData.access_token;
        console.log(`✅ Logged in as ${username}`);
    }
    
    get headers() {
        return {
            'Authorization': `Bearer ${this.token}`,
            'Content-Type': 'application/json'
        };
    }
    
    async createAIPersona(name, description, content) {
        const response = await fetch(`${this.baseUrl}/api/prompts`, {
            method: 'POST',
            headers: this.headers,
            body: JSON.stringify({ name, description, content })
        });
        
        const persona = await response.json();
        console.log(`✅ Created AI persona: ${name} (ID: ${persona.id})`);
        return persona.id;
    }
    
    async createSessionWithPersona(promptId) {
        const response = await fetch(`${this.baseUrl}/api/sessions`, {
            method: 'POST',
            headers: this.headers,
            body: JSON.stringify({ prompt_id: promptId })
        });
        
        const session = await response.json();
        console.log(`✅ Created session: ${session.id}`);
        return session.id;
    }
    
    async crawlWebsite(sessionId, url, maxDepth = 2) {
        const response = await fetch(`${this.baseUrl}/api/ingest/url`, {
            method: 'POST',
            headers: this.headers,
            body: JSON.stringify({
                session_id: sessionId,
                content_type: 'url',
                url: url,
                max_depth: maxDepth
            })
        });
        
        const result = await response.json();
        console.log(`✅ Website crawling started: ${url} (Doc ID: ${result.document_id})`);
        return result.document_id;
    }
    
    async waitForProcessing(sessionId, timeout = 60000) {
        console.log('⏳ Waiting for document processing...');
        const startTime = Date.now();
        
        while (Date.now() - startTime < timeout) {
            const response = await fetch(`${this.baseUrl}/api/documents/${sessionId}`, {
                headers: this.headers
            });
            const documents = await response.json();
            
            const processingDocs = documents.filter(doc => doc.processed === 'processing');
            if (processingDocs.length === 0) {
                console.log('✅ All documents processed');
                return true;
            }
            
            await new Promise(resolve => setTimeout(resolve, 5000));
        }
        
        console.log('⚠️ Timeout waiting for processing');
        return false;
    }
    
    async queryDocuments(query, sessionId = null, usePersona = true) {
        const queryData = {
            query: query,
            use_system_prompt: usePersona
        };
        if (sessionId) queryData.session_id = sessionId;

        const response = await fetch(`${this.baseUrl}/api/query`, {
            method: 'POST',
            headers: this.headers,
            body: JSON.stringify(queryData)
        });

        const result = await response.json();

        console.log('\n🤖 AI Response:');
        console.log(result.response);
        console.log(`\n📚 Based on ${result.sources.length} sources:`);
        result.sources.slice(0, 3).forEach((source, i) => {
            const metadata = source.metadata;
            const sourceInfo = metadata.filename || metadata.url || 'Unknown';
            console.log(`  ${i + 1}. ${sourceInfo}`);
        });

        return result;
    }

    async getChatHistory(sessionId) {
        const response = await fetch(`${this.baseUrl}/api/sessions/${sessionId}/messages`, {
            headers: this.headers
        });

        const messages = await response.json();

        console.log(`\n💬 Conversation History (${messages.length} messages):`);
        messages.forEach(msg => {
            const role = msg.role === 'user' ? '👤 User' : '🤖 AI';
            console.log(`\n${role}:`);
            console.log(`  ${msg.content.substring(0, 150)}...`);
        });

        return messages;
    }
}

// Usage example
async function main() {
    const client = new BrandGPTClient();
    
    // Authentication
    await client.registerAndLogin('demo_user', 'demo@example.com', 'secure_password123');
    
    // Create AI personas
    const businessPersonaId = await client.createAIPersona(
        'Business Analyst',
        'Expert in business analysis and strategy',
        'You are a business analyst. Focus on business impact, market insights, and strategic recommendations.'
    );
    
    // Create session and ingest content
    const sessionId = await client.createSessionWithPersona(businessPersonaId);
    await client.crawlWebsite(sessionId, 'https://en.wikipedia.org/wiki/Business_analysis');
    await client.waitForProcessing(sessionId);
    
    // Query with AI persona
    await client.queryDocuments(
        'What are the main methodologies mentioned for business analysis?',
        sessionId,
        true
    );

    // Multi-turn conversation
    console.log('\n' + '='.repeat(60));
    console.log('MULTI-TURN CONVERSATION DEMO:');
    console.log('='.repeat(60));

    await client.queryDocuments('What is the main topic?', sessionId, true);
    await client.queryDocuments('Can you provide more details about that?', sessionId, true);
    await client.queryDocuments('What are the practical applications?', sessionId, true);

    // View conversation history
    await client.getChatHistory(sessionId);
}

main().catch(console.error);
```

---

## 🐳 Docker Deployment

### Production Deployment

The application is designed for easy deployment using Docker with optimal networking configuration.

**Architecture:**
- **Host Networking**: Both app and Qdrant use host networking for optimal performance
- **Ollama Integration**: Seamless connection to Ollama running on host
- **Persistent Storage**: SQLite and Qdrant data preserved across restarts

### Quick Deployment

```bash
# Clone repository
git clone https://github.com/AIspezialisten/brandgpt_simple.git
cd brandgpt_simple

# Automated deployment
./deploy.sh
```

### Manual Deployment

```bash
# Ensure Ollama is running with models
ollama pull hf.co/Qwen/Qwen3-Embedding-8B-GGUF
ollama pull mistral-small:24b

# Create data directory
mkdir -p data

# Deploy services
docker-compose up -d

# Check status
docker-compose ps
curl http://localhost:9700/health
```

### Docker Compose Configuration

```yaml
services:
  app:
    build: .
    network_mode: host
    environment:
      - QDRANT_URL=http://localhost:6333
      - OLLAMA_BASE_URL=http://localhost:11434
      - API_HOST=0.0.0.0
      - API_PORT=9700
    volumes:
      - ./data:/app/data
    restart: unless-stopped

  qdrant:
    image: qdrant/qdrant:latest
    network_mode: host
    volumes:
      - qdrant_data:/qdrant/storage
    environment:
      - QDRANT__SERVICE__HTTP_PORT=6333
    restart: unless-stopped

volumes:
  qdrant_data:
```

### Service URLs
- **BrandGPT API**: http://localhost:9700
- **API Documentation**: http://localhost:9700/docs
- **Qdrant Dashboard**: http://localhost:6333/dashboard
- **Health Check**: http://localhost:9700/health

### Management Commands

```bash
# View logs
docker-compose logs -f

# Restart services
docker-compose restart

# Stop services
docker-compose down

# Update deployment
git pull
docker-compose down
docker-compose up -d --build

# Backup data
cp data/brandgpt.db data/backup-$(date +%Y%m%d).db
```

---

## 🧪 Testing

### Test Categories

The application includes comprehensive test coverage:

**Unit Tests:**
- Authentication and JWT handling
- Document processing (PDF, JSON, text, URL)
- Vector operations and similarity search
- RAG pipeline components

**Integration Tests:**
- End-to-end document ingestion workflows
- Complete RAG query pipelines
- Multi-user content isolation
- Session and persona management

**Performance Tests:**
- Load testing with multiple concurrent users
- Large document processing
- Query response times
- Vector search performance

### Running Tests

```bash
# Install test dependencies
uv pip install -e .

# Run all tests
uv run pytest tests/ -v

# Run specific test categories
python run_tests.py --suite auth          # Authentication tests
python run_tests.py --suite ingestion     # Document processing
python run_tests.py --suite query         # RAG pipeline tests
python run_tests.py --suite integration   # End-to-end tests
python run_tests.py --suite performance   # Performance tests

# Quick test run (skip slow tests)
python run_tests.py --suite all --fast

# Run with coverage report
python run_tests.py --suite all --coverage
```

### Test Configuration

Tests require running services:
```bash
# Start required services for testing
docker-compose up -d

# Set test environment variables
export TEST_API_URL=http://localhost:9700
export TEST_SKIP_SLOW=true  # Skip performance tests
```

---

## 📋 Environment Configuration

### Required Environment Variables

```bash
# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=hf.co/Qwen/Qwen3-Embedding-8B-GGUF
OLLAMA_LLM_MODEL=mistral-small:24b

# Qdrant Configuration
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION_NAME=brandgpt
QDRANT_VECTOR_SIZE=4096

# API Configuration
API_HOST=0.0.0.0
API_PORT=9700

# Security
SECRET_KEY=your-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Processing Configuration
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
MAX_FILE_SIZE_MB=100
RERANKER_TOP_K=5
RERANKER_CANDIDATES=20
```

### Development vs Production

**Development (.env):**
```bash
API_RELOAD=true
DEBUG=true
LOG_LEVEL=DEBUG
```

**Production (.env):**
```bash
API_RELOAD=false
DEBUG=false
LOG_LEVEL=INFO
SECRET_KEY=strong-random-secret-key
```

---

## 🔧 Troubleshooting

### Common Issues

**1. Cannot connect to Ollama**
```bash
# Check Ollama status
curl http://localhost:11434/api/tags

# Check required models
ollama list | grep -E "(qwen3|mistral-small)"

# Pull missing models
ollama pull hf.co/Qwen/Qwen3-Embedding-8B-GGUF
ollama pull mistral-small:24b
```

**2. Qdrant connection failed**
```bash
# Check Qdrant status
curl http://localhost:6333/collections

# Check Docker containers
docker-compose ps qdrant
docker-compose logs qdrant
```

**3. Document ingestion fails**
```bash
# Check processing status
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:9700/api/documents/$SESSION_ID

# Check application logs
docker-compose logs app | tail -50
```

**4. No search results returned**
```bash
# Verify documents are indexed
curl http://localhost:6333/collections/brandgpt

# Check user isolation
# Make sure you're querying with the same user who uploaded documents
```

### Debug Mode

Enable debug logging for detailed troubleshooting:

```bash
# Set debug environment
export DEBUG=true
export LOG_LEVEL=DEBUG

# Restart application
docker-compose restart app

# View detailed logs
docker-compose logs -f app
```

---

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines:

1. **Fork the repository**
2. **Create feature branch**: `git checkout -b feature/amazing-feature`
3. **Run tests**: `python run_tests.py --suite all`
4. **Commit changes**: `git commit -m 'Add amazing feature'`
5. **Push to branch**: `git push origin feature/amazing-feature`
6. **Open Pull Request**

### Development Setup

```bash
# Clone your fork
git clone https://github.com/yourusername/brandgpt_simple.git
cd brandgpt_simple

# Install development dependencies
uv pip install -e ".[dev]"

# Setup pre-commit hooks
pre-commit install

# Run tests
python run_tests.py --suite all
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **LangChain & LangGraph**: Advanced RAG pipeline orchestration
- **Ollama**: Local LLM and embedding model serving
- **Qdrant**: High-performance vector database
- **FastAPI**: Modern, fast web framework for APIs
- **The Open Source Community**: For the amazing tools and libraries

---

## 📞 Support

For support and questions:

- **Documentation**: Check this README and `/docs` endpoint
- **Issues**: Open an issue on GitHub
- **Discussions**: Use GitHub Discussions for questions

---

*Built with ❤️ using modern AI and vector search technologies*