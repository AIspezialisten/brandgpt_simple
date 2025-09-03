# BrandGPT CLI

A comprehensive command-line interface for interacting with the BrandGPT RAG API.

## Installation

```bash
npm install -g @marcapo/brandgpt-client
```

Or for local development:

```bash
npm run build
npm link
```

## Quick Start

1. **Login to get started:**
```bash
brandgpt auth login
```

2. **Create a session:**
```bash
brandgpt sessions create --name "My Project"
```

3. **Upload documents:**
```bash
brandgpt ingest file document.pdf --session <session-id>
```

4. **Ask questions:**
```bash
brandgpt query ask "What is this document about?" --session <session-id>
```

## Commands

### Authentication (`brandgpt auth`)

```bash
# Login with username/password
brandgpt auth login

# Register new account
brandgpt auth register

# Set API key manually
brandgpt auth set-key

# Generate new API key
brandgpt auth generate-key

# Show current user
brandgpt auth whoami

# Logout
brandgpt auth logout
```

### Session Management (`brandgpt sessions`)

```bash
# List all sessions
brandgpt sessions list

# Create new session
brandgpt sessions create --name "My Session"

# Get session details
brandgpt sessions get <session-id>

# Update session name
brandgpt sessions update <session-id> --name "New Name"

# Delete session
brandgpt sessions delete <session-id>

# List documents in session
brandgpt sessions docs <session-id>
```

### Data Ingestion (`brandgpt ingest`)

```bash
# Upload a file
brandgpt ingest file document.pdf --session <session-id>

# Scrape a URL
brandgpt ingest url https://example.com --session <session-id>

# Ingest structured JSON data
brandgpt ingest data data.json --session <session-id>

# Batch upload files from directory
brandgpt ingest batch ./documents --session <session-id>

# Check processing status
brandgpt ingest status <session-id>
```

### Querying (`brandgpt query`)

```bash
# Ask a question
brandgpt query ask "What is the main topic?" --session <session-id>

# Interactive chat mode
brandgpt query chat --session <session-id>

# Search for specific terms
brandgpt query search "machine learning" --session <session-id>

# Batch queries from file
brandgpt query batch questions.txt --session <session-id>
```

## Configuration

### Config Commands

```bash
# Show current configuration
brandgpt config show

# Set configuration values
brandgpt config set baseUrl "https://api.brandgpt.com"
brandgpt config set defaultTimeout 30000
brandgpt config set outputFormat "json"

# Clear all configuration
brandgpt config clear

# Show config file location
brandgpt --config-path
```

### Configuration File

The CLI stores configuration in `~/.brandgpt/config.json`:

```json
{
  "baseUrl": "https://api.brandgpt.com",
  "apiKey": "bgpt_...",
  "defaultTimeout": 30000,
  "outputFormat": "table"
}
```

## Output Formats

All commands support multiple output formats:

- `--format json` - JSON output
- `--format table` - Formatted table (default)
- `--format yaml` - YAML output

## Examples

### Complete Workflow

```bash
# 1. Login
brandgpt auth login

# 2. Create session
SESSION_ID=$(brandgpt sessions create --name "Research Project" --format json | jq -r '.id')

# 3. Upload documents
brandgpt ingest file research.pdf --session $SESSION_ID
brandgpt ingest url https://research-site.com --session $SESSION_ID

# 4. Wait for processing
brandgpt ingest status $SESSION_ID

# 5. Ask questions
brandgpt query ask "What are the key findings?" --session $SESSION_ID

# 6. Interactive chat
brandgpt query chat --session $SESSION_ID
```

### Batch Processing

```bash
# Upload all PDFs in a directory
brandgpt ingest batch ./documents --session $SESSION_ID --pattern "*.pdf" --recursive

# Run multiple queries
echo "What is the main topic?
What are the key findings?
What are the recommendations?" > questions.txt

brandgpt query batch questions.txt --session $SESSION_ID --output results.json
```

### Advanced Querying

```bash
# Filter by group
brandgpt ingest file doc1.pdf --session $SESSION_ID --group-id "legal"
brandgpt ingest file doc2.pdf --session $SESSION_ID --group-id "technical"

brandgpt query ask "Legal requirements?" --session $SESSION_ID --group-id "legal"

# Search with similarity threshold
brandgpt query search "machine learning" --session $SESSION_ID --threshold 0.8

# Limit results
brandgpt query ask "Summary?" --session $SESSION_ID --max-results 3
```

## Troubleshooting

### Common Issues

1. **Authentication Error**
   ```bash
   brandgpt auth whoami  # Check if logged in
   brandgpt auth login   # Re-login if needed
   ```

2. **Server Connection Issues**
   ```bash
   brandgpt health --server https://your-server.com
   ```

3. **File Upload Failures**
   ```bash
   # Check file exists and permissions
   ls -la document.pdf
   
   # Try with explicit session
   brandgpt ingest file document.pdf --session <session-id>
   ```

4. **Processing Status**
   ```bash
   # Check if documents are still processing
   brandgpt ingest status <session-id>
   
   # Use --wait flag to wait for completion
   brandgpt ingest file doc.pdf --session <session-id> --wait
   ```

### Debug Mode

Enable detailed logging:

```bash
brandgpt --debug query ask "test question" --session <session-id>
```

### Configuration Issues

```bash
# Show config location and contents
brandgpt --config-path
brandgpt config show

# Reset configuration
brandgpt config clear
brandgpt auth login
```

## API Compatibility

The CLI supports all BrandGPT API endpoints:

- ✅ Authentication (login, register, API keys)
- ✅ Session management
- ✅ File upload (PDF, text, JSON)
- ✅ URL scraping
- ✅ Structured data ingestion
- ✅ RAG querying
- ✅ Document management
- ✅ Health checks

## Development

### Running from Source

```bash
# Install dependencies
npm install

# Build TypeScript
npm run build

# Run CLI
./bin/brandgpt-cli.js --help

# Or use ts-node for development
npm install -g ts-node typescript
./bin/brandgpt-cli.js --help
```

### Testing

```bash
# Test against local server
brandgpt health --server http://localhost:9700

# Run full integration test
npm run test
```

## Support

- **Documentation**: See README.md for API client usage
- **Issues**: Report bugs and feature requests on GitHub
- **Examples**: Check the `examples/` directory for more usage patterns