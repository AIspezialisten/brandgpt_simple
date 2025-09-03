# BrandGPT Node.js Client

A comprehensive Node.js/TypeScript client library for the BrandGPT RAG (Retrieval-Augmented Generation) API.

## Features

- 🚀 **Complete API Coverage** - All BrandGPT endpoints supported
- 📝 **TypeScript Support** - Full type definitions included
- 🔐 **Authentication** - JWT and API key authentication
- 📄 **File Upload** - Support for PDF and text file ingestion
- 🌐 **URL Scraping** - Ingest content from web URLs
- 📊 **Structured Data** - JSON object/array ingestion
- 🔍 **RAG Queries** - Query ingested content with context
- ⚡ **Modern Async/Await** - Promise-based API
- 🛡️ **Error Handling** - Comprehensive error types and handling
- 🖥️ **CLI Interface** - Full-featured command-line interface
- 📚 **Batch Operations** - Process multiple files and queries
- 🎨 **Multiple Output Formats** - JSON, Table, and YAML support

## Installation

### Library Installation

```bash
npm install @marcapo/brandgpt-client
```

### CLI Installation (Global)

```bash
npm install -g @marcapo/brandgpt-client
```

After installation, the CLI is available as `brandgpt` command:

```bash
brandgpt --help
brandgpt auth login
brandgpt sessions create --name "My Session"
```

## Quick Start

```typescript
import { BrandGPTClient } from '@marcapo/brandgpt-client';

const client = new BrandGPTClient({
  baseUrl: 'https://api.brandgpt.com',
  apiKey: 'your-api-key-here'
});

// Create a session
const session = await client.sessions.create({ name: 'My Session' });

// Upload a document
const fs = require('fs');
const fileBuffer = fs.readFileSync('document.pdf');
const uploadResult = await client.ingestion.uploadFile(
  fileBuffer,
  'document.pdf',
  session.id
);

// Query the content
const response = await client.query.query({
  query: 'What is this document about?',
  sessionId: session.id
});

console.log('Answer:', response.response);
console.log('Sources:', response.sources);
```

## API Reference

### Authentication

```typescript
// Register a new user
const user = await client.auth.register({
  username: 'john_doe',
  email: 'john@example.com',
  password: 'secure_password'
});

// Login with username/password
const token = await client.auth.login({
  username: 'john_doe',
  password: 'secure_password'
});

// Generate an API key
const apiKey = await client.auth.generateApiKey();
client.setApiKey(apiKey.api_key);

// Get current user info
const currentUser = await client.auth.getCurrentUser();
```

### Session Management

```typescript
// Create a session
const session = await client.sessions.create({
  name: 'My Research Session'
});

// List all sessions
const sessions = await client.sessions.list();
```

### Content Ingestion

#### File Upload
```typescript
import fs from 'fs';

// Upload a PDF or text file
const fileBuffer = fs.readFileSync('document.pdf');
const result = await client.ingestion.uploadFile(
  fileBuffer,
  'document.pdf',
  session.id,
  { groupId: 'research-docs' }
);
```

#### URL Scraping
```typescript
// Ingest content from a URL
const result = await client.ingestion.ingestUrl(
  'https://example.com/article',
  {
    maxDepth: 2,
    maxLinksPerPage: 10,
    sessionId: session.id,
    groupId: 'web-content'
  }
);
```

#### Structured Data
```typescript
// Ingest JSON data
const result = await client.ingestion.ingestStructuredData({
  data: {
    product_name: 'iPhone 15',
    category: 'Smartphones',
    features: ['A17 Pro chip', '48MP camera', 'USB-C'],
    price: 999
  },
  sessionId: session.id,
  groupId: 'products',
  metadata: { source: 'product-catalog' }
});
```

### Querying Content

```typescript
// Perform a RAG query
const response = await client.query.query({
  query: 'What are the key features of the iPhone 15?',
  sessionId: session.id,
  maxResults: 5
});

console.log('Answer:', response.response);
response.sources.forEach(source => {
  console.log('Source:', source.metadata.filename);
  console.log('Text:', source.text);
});
```

### Document Management

```typescript
// List documents in a session
const documents = await client.documents.listBySession(session.id);

// Delete documents by various criteria
await client.documents.delete({
  groupId: 'old-docs'  // Delete all docs in this group
});

await client.documents.delete({
  documentId: 123  // Delete specific document
});

await client.documents.delete({
  sessionId: session.id  // Delete all docs in session
});
```

### Prompt Templates

```typescript
// Create a prompt template
const prompt = await client.prompts.create({
  name: 'Product Analysis',
  description: 'Analyze product features and benefits',
  content: 'Analyze this product: {query}. Focus on features, benefits, and target audience.'
});

// List all prompts
const prompts = await client.prompts.list();
```

## Configuration

```typescript
const client = new BrandGPTClient({
  baseUrl: 'https://api.brandgpt.com',  // API base URL
  apiKey: 'your-api-key',               // Optional: API key for auth
  timeout: 30000                        // Optional: Request timeout in ms
});
```

## Error Handling

```typescript
import { BrandGPTError } from '@marcapo/brandgpt-client';

try {
  const result = await client.query.query({
    query: 'Test query',
    sessionId: 'invalid-session'
  });
} catch (error) {
  if (error instanceof BrandGPTError) {
    console.error('API Error:', error.message);
    console.error('Status Code:', error.statusCode);
    console.error('Details:', error.details);
  } else {
    console.error('Unknown error:', error);
  }
}
```

## TypeScript Support

All types are fully typed and exported:

```typescript
import {
  BrandGPTClient,
  Session,
  Document,
  QueryResponse,
  IngestionStatus,
  BrandGPTError
} from '@marcapo/brandgpt-client';

const client: BrandGPTClient = new BrandGPTClient({...});
const session: Session = await client.sessions.create({...});
const response: QueryResponse = await client.query.query({...});
```

## Command Line Interface (CLI)

The BrandGPT Node.js client includes a powerful CLI for document analysis workflows. Perfect for automation, batch processing, and interactive document exploration.

### CLI Quick Start

```bash
# Install globally
npm install -g @marcapo/brandgpt-client

# Health check
brandgpt health --server https://api.brandgpt.com

# Login or register
brandgpt auth login

# Create a session
brandgpt sessions create --name "Document Analysis"

# Upload documents
brandgpt ingest file document.pdf --session <session-id>
brandgpt ingest batch ./documents --session <session-id> --pattern "*.pdf"

# Query your documents
brandgpt query ask "What are the key findings?" --session <session-id>
brandgpt query chat --session <session-id>  # Interactive chat
```

### CLI Features

- **🔐 Authentication Management**: Login, register, API key management
- **📁 Session Organization**: Create, manage, and organize document sessions  
- **📄 Multi-format Ingestion**: PDF, text, JSON, URLs with batch processing
- **🤖 Intelligent Querying**: Q&A, search, interactive chat, batch queries
- **⚙️ Configuration Management**: Persistent settings and preferences
- **📊 Multiple Output Formats**: JSON, formatted tables, YAML
- **🎯 Group-based Organization**: Organize content with group IDs
- **⏱️ Progress Tracking**: Real-time status and processing indicators

### CLI Command Structure

```bash
brandgpt <command> <subcommand> [options] [arguments]

# Main command groups:
brandgpt auth      # Authentication and user management
brandgpt sessions  # Session management  
brandgpt ingest    # Document ingestion
brandgpt query     # Querying and search
brandgpt config    # Configuration management
brandgpt health    # Server health checks
```

### Example Workflows

#### Research Paper Analysis
```bash
# Setup
brandgpt auth login
SESSION_ID=$(brandgpt sessions create --name "AI Research" --format json | jq -r '.id')

# Upload papers with organization
brandgpt ingest file "transformer-paper.pdf" --session $SESSION_ID --group-id "nlp"
brandgpt ingest file "vision-paper.pdf" --session $SESSION_ID --group-id "cv"

# Analyze content
brandgpt query ask "What are the main contributions?" --session $SESSION_ID
brandgpt query search "attention mechanism" --session $SESSION_ID --group-id "nlp"
```

#### Legal Document Review
```bash
# Process contracts with batch upload
brandgpt ingest batch ./contracts --session $SESSION_ID --pattern "*.pdf"

# Extract key information
echo "What are the key terms and conditions?
What are the termination clauses?
What liability limitations exist?" > questions.txt

brandgpt query batch questions.txt --session $SESSION_ID --output analysis.json
```

#### Interactive Support Knowledge Base
```bash
# Build knowledge base from multiple sources
brandgpt ingest url "https://docs.company.com" --session $SESSION_ID --depth 3
brandgpt ingest batch ./support-docs --session $SESSION_ID

# Interactive support session
brandgpt query chat --session $SESSION_ID
# > How do I reset my password?
# > What are the system requirements?
# > exit
```

### Advanced CLI Features

#### Batch Processing with Automation
```bash
#!/bin/bash
# Automated daily document processing
SESSION_NAME="Daily-Reports-$(date +%Y-%m-%d)"
SESSION_ID=$(brandgpt sessions create --name "$SESSION_NAME" --format json | jq -r '.id')

# Process all new documents
for file in /path/to/daily/reports/*.pdf; do
    brandgpt ingest file "$file" --session $SESSION_ID --wait
done

# Generate summary
brandgpt query ask "Provide an executive summary of today's reports" \
    --session $SESSION_ID --format json > "summary-$(date +%Y%m%d).json"
```

#### Multi-language Processing
```bash
# Organize by language/region
brandgpt ingest file "report-en.pdf" --session $SESSION_ID --group-id "english"
brandgpt ingest file "rapport-fr.pdf" --session $SESSION_ID --group-id "french"

# Cross-language analysis
brandgpt query ask "What trends appear across all regions?" --session $SESSION_ID
```

#### Output Format Control
```bash
# Different formats for different use cases
brandgpt sessions list --format table    # Human readable
brandgpt sessions list --format json     # For scripts/parsing  
brandgpt sessions list --format yaml     # For configuration

# Piping and processing
brandgpt query ask "Summary" --session $SESSION_ID --format json | \
    jq -r '.response' > summary.txt
```

### CLI Documentation

- **📖 Complete CLI Guide**: [docs/CLI.md](docs/CLI.md) - Comprehensive command reference
- **🎓 Interactive Tutorial**: [docs/CLI-TUTORIAL.md](docs/CLI-TUTORIAL.md) - Step-by-step examples
- **📋 Man Page**: [docs/brandgpt.1](docs/brandgpt.1) - Traditional Unix manual page
- **🔧 Built-in Help**: `brandgpt --help` and `brandgpt <command> --help`

### Configuration

CLI settings are stored in `~/.brandgpt/config.json`:

```bash
# View current configuration
brandgpt config show

# Set server URL
brandgpt config set baseUrl "https://your-server.com"

# Show config file location
brandgpt --config-path
```

## Examples

Check the `examples/` directory for complete usage examples:

- `basic-usage.js` - Complete workflow example
- `file-ingestion.js` - File upload examples
- `structured-data.js` - JSON ingestion examples

## Development

```bash
# Install dependencies
npm install

# Build the library
npm run build

# Run tests
npm test

# Watch mode for development
npm run dev
```

## License

MIT

## Support

For issues and questions, please visit the [GitHub repository](https://github.com/marcapo/brandgpt-nodejs-client) or contact support.