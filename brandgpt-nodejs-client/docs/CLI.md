# BrandGPT CLI Documentation

The BrandGPT CLI is a comprehensive command-line interface for interacting with the BrandGPT RAG API. It provides all the functionality needed to manage authentication, sessions, document ingestion, and querying from the command line.

## Table of Contents

- [Installation](#installation)
- [Getting Started](#getting-started)
- [Authentication](#authentication)
- [Session Management](#session-management)
- [Data Ingestion](#data-ingestion)
- [Querying and Search](#querying-and-search)
- [Configuration](#configuration)
- [Global Options](#global-options)
- [Output Formats](#output-formats)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)
- [Advanced Usage](#advanced-usage)

## Installation

### Global Installation (Recommended)

```bash
npm install -g @marcapo/brandgpt-client
```

### Local Installation

```bash
npm install @marcapo/brandgpt-client
npx brandgpt --help
```

### From Source

```bash
git clone https://github.com/marcapo/brandgpt-nodejs-client.git
cd brandgpt-nodejs-client
npm install
npm run build
npm link
```

## Getting Started

1. **Check server connectivity**:
   ```bash
   brandgpt health --server https://your-brandgpt-server.com
   ```

2. **Login or register**:
   ```bash
   brandgpt auth login
   # or
   brandgpt auth register
   ```

3. **Create your first session**:
   ```bash
   brandgpt sessions create --name "My First Session"
   ```

4. **Upload a document**:
   ```bash
   brandgpt ingest file document.pdf --session <session-id>
   ```

5. **Ask questions**:
   ```bash
   brandgpt query ask "What is this document about?" --session <session-id>
   ```

## Authentication

The CLI supports multiple authentication methods and user management features.

### Commands

#### `brandgpt auth login`

Login with username and password. Optionally generates and saves an API key for future use.

```bash
brandgpt auth login
brandgpt auth login -u username -p password -s https://api.brandgpt.com
```

**Options:**
- `-u, --username <username>` - Username (will prompt if not provided)
- `-p, --password <password>` - Password (will prompt if not provided)  
- `-s, --server <url>` - BrandGPT server URL

**Interactive Flow:**
1. Prompts for missing credentials
2. Authenticates with server
3. Displays user information
4. Offers to generate and save API key
5. Saves server URL to configuration

#### `brandgpt auth register`

Register a new user account with validation and auto-login option.

```bash
brandgpt auth register
brandgpt auth register -u newuser -e user@example.com -p password
```

**Options:**
- `-u, --username <username>` - Username (min 3 characters)
- `-e, --email <email>` - Email address (validated)
- `-p, --password <password>` - Password (min 6 characters)
- `-s, --server <url>` - BrandGPT server URL

**Features:**
- Input validation (username length, email format, password strength)
- Auto-login option after registration
- Automatic API key generation

#### `brandgpt auth set-key`

Manually set an API key for authentication.

```bash
brandgpt auth set-key
brandgpt auth set-key -k bgpt_your_api_key_here
```

**Options:**
- `-k, --key <apikey>` - API key (will prompt if not provided)

**Validation:**
- Ensures API key starts with "bgpt_"
- Securely stores in configuration

#### `brandgpt auth generate-key`

Generate a new API key using existing authentication.

```bash
brandgpt auth generate-key
brandgpt auth generate-key -s https://api.brandgpt.com
```

**Options:**
- `-s, --server <url>` - BrandGPT server URL

**Requirements:**
- Must be already authenticated
- Replaces existing API key

#### `brandgpt auth whoami`

Display current user information.

```bash
brandgpt auth whoami
brandgpt auth whoami --format json
```

**Options:**
- `--format <format>` - Output format: `json`, `table`, `yaml` (default: `table`)
- `-s, --server <url>` - BrandGPT server URL

#### `brandgpt auth logout`

Clear stored authentication credentials.

```bash
brandgpt auth logout
```

**Features:**
- Confirmation prompt for safety
- Preserves server URL configuration
- Removes only API key

## Session Management

Sessions organize your documents and maintain conversation context for queries.

### Commands

#### `brandgpt sessions list`

List all sessions for the current user.

```bash
brandgpt sessions list
brandgpt sessions ls --format json --limit 10
```

**Options:**
- `--format <format>` - Output format: `json`, `table`, `yaml` (default: `table`)
- `--limit <number>` - Limit number of sessions displayed

**Aliases:** `ls`

#### `brandgpt sessions create`

Create a new session.

```bash
brandgpt sessions create --name "Research Project"
brandgpt sessions create  # Interactive prompt for name
```

**Options:**
- `-n, --name <name>` - Session name (will prompt if not provided)
- `--format <format>` - Output format for created session

**Features:**
- Name validation (non-empty)
- Returns session ID for use in other commands

#### `brandgpt sessions get`

Get detailed information about a specific session.

```bash
brandgpt sessions get session-id-here
brandgpt sessions get session-id-here --include-docs --format json
```

**Options:**
- `--format <format>` - Output format
- `--include-docs` - Include list of documents in the session

#### `brandgpt sessions update`

Update session name.

```bash
brandgpt sessions update session-id-here --name "New Name"
brandgpt sessions update session-id-here  # Interactive prompt
```

**Options:**
- `-n, --name <name>` - New session name
- `--format <format>` - Output format

#### `brandgpt sessions delete`

Delete a session and all its documents.

```bash
brandgpt sessions delete session-id-here
brandgpt sessions rm session-id-here --force  # Skip confirmation
```

**Options:**
- `-f, --force` - Skip confirmation prompt

**Aliases:** `rm`

**Safety Features:**
- Shows session name and document count before deletion
- Confirmation prompt (unless `--force` used)
- Permanent deletion warning

#### `brandgpt sessions docs`

List all documents in a specific session.

```bash
brandgpt sessions docs session-id-here
brandgpt sessions docs session-id-here --format json
```

**Options:**
- `--format <format>` - Output format

## Data Ingestion

The CLI supports multiple data ingestion methods with progress tracking and batch operations.

### Commands

#### `brandgpt ingest file`

Upload and process a single file.

```bash
brandgpt ingest file document.pdf --session session-id
brandgpt ingest file data.json --session session-id --group-id "research" --wait
```

**Options:**
- `-s, --session <session-id>` - Session ID (required)
- `-g, --group-id <group-id>` - Group ID for content organization
- `--format <format>` - Output format
- `--wait` - Wait for processing to complete

**Supported File Types:**
- PDF documents
- Text files (.txt, .md)
- JSON files
- And more...

**Features:**
- File validation and size reporting
- Progress indicators
- Optional processing completion waiting
- Error handling with detailed messages

#### `brandgpt ingest url`

Scrape and ingest content from a URL.

```bash
brandgpt ingest url https://example.com --session session-id
brandgpt ingest url https://docs.site.com --session session-id --depth 3 --wait
```

**Options:**
- `-s, --session <session-id>` - Session ID (required)
- `-g, --group-id <group-id>` - Group ID for content organization
- `-d, --depth <depth>` - Scraping depth (default: 1)
- `--format <format>` - Output format
- `--wait` - Wait for processing to complete

**Features:**
- URL validation
- Configurable scraping depth
- Progress tracking
- Extended timeout for complex sites

#### `brandgpt ingest data`

Ingest structured JSON data.

```bash
brandgpt ingest data data.json --session session-id
echo '{"key": "value"}' | brandgpt ingest data --stdin --session session-id
brandgpt ingest data --session session-id  # Interactive editor mode
```

**Options:**
- `-s, --session <session-id>` - Session ID (required)
- `-g, --group-id <group-id>` - Group ID for content organization
- `--format <format>` - Output format
- `--stdin` - Read JSON from standard input

**Input Methods:**
1. **File**: Specify JSON file path
2. **Stdin**: Pipe JSON data using `--stdin`
3. **Interactive**: Opens default editor for JSON input

**Features:**
- JSON validation
- Metadata tagging
- Flexible input options

#### `brandgpt ingest batch`

Upload multiple files from a directory.

```bash
brandgpt ingest batch ./documents --session session-id
brandgpt ingest batch ./pdfs --session session-id --pattern "*.pdf" --recursive
```

**Options:**
- `-s, --session <session-id>` - Session ID (required)
- `-g, --group-id <group-id>` - Group ID for all files
- `--pattern <pattern>` - File pattern to match (default: `*`)
- `--recursive` - Process subdirectories
- `--format <format>` - Output format for results

**Features:**
- Pattern-based file filtering
- Recursive directory processing
- Progress reporting for each file
- Success/failure tracking
- Continues processing on individual file errors

#### `brandgpt ingest status`

Check processing status of documents in a session.

```bash
brandgpt ingest status session-id
brandgpt ingest status session-id --format json
```

**Options:**
- `--format <format>` - Output format

**Output Information:**
- Document ID and filename
- Content type
- Processing status (Yes/Pending)
- Creation timestamp
- Summary statistics

## Querying and Search

The CLI provides multiple ways to interact with your ingested content.

### Commands

#### `brandgpt query ask`

Ask questions about your documents with context-aware responses.

```bash
brandgpt query ask "What are the key findings?" --session session-id
brandgpt query ask --session session-id  # Interactive mode
```

**Options:**
- `-s, --session <session-id>` - Session ID (required)
- `-g, --group-id <group-id>` - Filter by specific group
- `-m, --max-results <number>` - Maximum sources to retrieve (default: 5)
- `--format <format>` - Output format
- `--sources-only` - Show only sources without generated answer
- `--no-sources` - Hide source references

**Features:**
- Interactive mode when no question provided
- Rich formatted output with sources
- Response time measurement
- Source attribution with relevance scores

#### `brandgpt query search`

Search for specific terms in documents.

```bash
brandgpt query search "machine learning" --session session-id
brandgpt query search "API documentation" --session session-id --threshold 0.8
```

**Options:**
- `-s, --session <session-id>` - Session ID (required)
- `-g, --group-id <group-id>` - Filter by specific group
- `-m, --max-results <number>` - Maximum results (default: 10)
- `--format <format>` - Output format
- `--threshold <score>` - Minimum similarity score 0-1 (default: 0.7)

**Features:**
- Semantic similarity search
- Configurable similarity threshold
- Source metadata and previews
- Relevance scoring

#### `brandgpt query chat`

Start an interactive chat session.

```bash
brandgpt query chat --session session-id
brandgpt query chat --session session-id --group-id "technical"
```

**Options:**
- `-s, --session <session-id>` - Session ID (required)
- `-g, --group-id <group-id>` - Filter by specific group
- `-m, --max-results <number>` - Maximum sources per query

**Interactive Commands:**
- `exit` or `quit` - End chat session
- `help` - Show available commands
- Any other input - Treated as a question

**Features:**
- Persistent conversation context
- Real-time response timing
- Source attribution
- Graceful exit handling

#### `brandgpt query batch`

Run multiple queries from a file.

```bash
echo -e "What is the main topic?\nWhat are the conclusions?" > questions.txt
brandgpt query batch questions.txt --session session-id --output results.json
```

**Options:**
- `-s, --session <session-id>` - Session ID (required)
- `-g, --group-id <group-id>` - Filter by specific group
- `-m, --max-results <number>` - Maximum sources per query
- `--output <file>` - Save results to file
- `--format <format>` - Output format (default: json)
- `--delay <ms>` - Delay between queries (default: 1000ms)

**File Format:**
- One question per line
- Empty lines ignored
- Lines starting with # treated as comments

**Features:**
- Progress tracking
- Error handling per query
- Configurable delays to avoid rate limiting
- Comprehensive results with timestamps

## Configuration

Manage CLI settings and preferences.

### Commands

#### `brandgpt config show`

Display current configuration with masked sensitive data.

```bash
brandgpt config show
brandgpt config show --format json
```

**Options:**
- `--format <format>` - Output format

**Security:**
- API keys are masked (shows first 8 characters + "...")
- Full configuration structure displayed

#### `brandgpt config set`

Update configuration values.

```bash
brandgpt config set baseUrl "https://api.brandgpt.com"
brandgpt config set defaultTimeout 30000
brandgpt config set outputFormat "json"
```

**Valid Keys:**
- `baseUrl` - Default server URL
- `defaultTimeout` - Request timeout in milliseconds  
- `outputFormat` - Default output format

**Validation:**
- Key name validation
- Type conversion for numeric values

#### `brandgpt config clear`

Reset all configuration to defaults.

```bash
brandgpt config clear
```

**Features:**
- Confirmation prompt for safety
- Complete configuration reset
- Preserves directory structure

### Configuration File

Location: `~/.brandgpt/config.json`

```json
{
  "baseUrl": "https://api.brandgpt.com",
  "apiKey": "bgpt_...",
  "defaultTimeout": 30000,
  "outputFormat": "table"
}
```

## Global Options

These options work with any command:

### `--config-path`

Show the configuration file path.

```bash
brandgpt --config-path
```

### `--debug`

Enable detailed debug output.

```bash
brandgpt --debug query ask "test" --session session-id
```

### `--help`

Show help information.

```bash
brandgpt --help
brandgpt auth --help
brandgpt query ask --help
```

### `--version`

Show CLI version.

```bash
brandgpt --version
```

## Output Formats

The CLI supports three output formats:

### Table Format (Default)

Human-readable tabular output with borders and formatting.

```bash
brandgpt sessions list --format table
```

### JSON Format

Machine-readable JSON output, optionally pretty-printed.

```bash
brandgpt sessions list --format json
```

### YAML Format

Human-readable YAML output.

```bash
brandgpt sessions list --format yaml
```

## Examples

### Complete Workflow Example

```bash
# 1. Health check
brandgpt health --server https://api.brandgpt.com

# 2. Register or login
brandgpt auth register
# or
brandgpt auth login

# 3. Create a session
SESSION_ID=$(brandgpt sessions create --name "Research Project" --format json | jq -r '.id')

# 4. Upload documents
brandgpt ingest file research.pdf --session $SESSION_ID
brandgpt ingest url https://research-site.com --session $SESSION_ID --depth 2
brandgpt ingest batch ./documents --session $SESSION_ID --pattern "*.pdf"

# 5. Wait for processing
brandgpt ingest status $SESSION_ID

# 6. Query the data
brandgpt query ask "What are the main findings?" --session $SESSION_ID
brandgpt query search "methodology" --session $SESSION_ID
brandgpt query chat --session $SESSION_ID
```

### Batch Processing Example

```bash
# Create questions file
cat > questions.txt << EOF
What is the main topic of these documents?
What methodology was used?
What are the key findings?
What are the limitations?
What are the recommendations?
EOF

# Run batch queries
brandgpt query batch questions.txt \
  --session $SESSION_ID \
  --output results.json \
  --format json

# Process results
jq '.[] | {question: .question, answer: .response}' results.json
```

### Advanced Data Organization

```bash
# Organize by groups
brandgpt ingest file legal.pdf --session $SESSION_ID --group-id "legal"
brandgpt ingest file technical.pdf --session $SESSION_ID --group-id "technical"
brandgpt ingest file marketing.pdf --session $SESSION_ID --group-id "marketing"

# Query specific groups
brandgpt query ask "Legal requirements?" --session $SESSION_ID --group-id "legal"
brandgpt query ask "Technical specifications?" --session $SESSION_ID --group-id "technical"
```

### Automation Example

```bash
#!/bin/bash
# Automated document processing script

SESSION_NAME="Daily Report $(date +%Y-%m-%d)"
SESSION_ID=$(brandgpt sessions create --name "$SESSION_NAME" --format json | jq -r '.id')

# Process all new documents
for file in /path/to/new/documents/*.pdf; do
  echo "Processing $file..."
  brandgpt ingest file "$file" --session $SESSION_ID --wait
done

# Generate summary
brandgpt query ask "Provide a summary of all documents" \
  --session $SESSION_ID \
  --format json > "summary-$(date +%Y%m%d).json"

echo "Session ID: $SESSION_ID"
```

## Troubleshooting

### Common Issues

#### Authentication Errors

```bash
❌ No authentication found. Please login first.
```

**Solution:**
```bash
brandgpt auth login
# or
brandgpt auth set-key --key your-api-key
```

#### Server Connection Issues

```bash
❌ Health check failed: connect ECONNREFUSED
```

**Solutions:**
1. Check server URL: `brandgpt config show`
2. Test connectivity: `brandgpt health --server https://correct-url.com`
3. Update configuration: `brandgpt config set baseUrl "https://correct-url.com"`

#### File Upload Failures

```bash
❌ File not found: document.pdf
```

**Solutions:**
1. Check file path: `ls -la document.pdf`
2. Use absolute paths: `brandgpt ingest file /full/path/to/document.pdf`
3. Check permissions: `chmod 644 document.pdf`

#### Session Not Found

```bash
❌ Session not found: invalid-session-id
```

**Solutions:**
1. List available sessions: `brandgpt sessions list`
2. Create new session: `brandgpt sessions create --name "My Session"`

### Debug Mode

Enable detailed logging for troubleshooting:

```bash
brandgpt --debug auth login
brandgpt --debug ingest file document.pdf --session session-id
```

### Configuration Issues

Reset configuration if corrupted:

```bash
brandgpt config clear
brandgpt auth login  # Re-authenticate
```

Check configuration location:
```bash
brandgpt --config-path
cat ~/.brandgpt/config.json
```

## Advanced Usage

### Environment Variables

You can set default values using environment variables:

```bash
export BRANDGPT_BASE_URL="https://api.brandgpt.com"
export BRANDGPT_API_KEY="bgpt_your_key_here"
export DEBUG=1  # Enable debug mode
```

### Scripting Integration

The CLI is designed for scripting and automation:

```bash
# Check if authenticated
if brandgpt auth whoami > /dev/null 2>&1; then
  echo "Authenticated"
else
  echo "Not authenticated"
  brandgpt auth login
fi

# Process with error handling
if brandgpt ingest file "$FILE" --session "$SESSION_ID"; then
  echo "Upload successful"
else
  echo "Upload failed"
  exit 1
fi
```

### Performance Tips

1. **Use batch operations** for multiple files
2. **Enable --wait** only when necessary (processing can be slow)
3. **Use --format json** for parsing results in scripts  
4. **Set appropriate --max-results** to limit response size
5. **Use --group-id** to organize and filter content efficiently

### Integration with Other Tools

#### With jq (JSON processing)

```bash
# Get session IDs
brandgpt sessions list --format json | jq -r '.[].id'

# Extract specific fields
brandgpt query ask "summary" --session $SESSION_ID --format json | \
  jq -r '.response'
```

#### With curl (API comparison)

```bash
# CLI approach
brandgpt health --server https://api.brandgpt.com

# Direct API approach
curl https://api.brandgpt.com/health
```

#### With watch (Monitoring)

```bash
# Monitor processing status
watch -n 5 'brandgpt ingest status session-id'

# Monitor sessions
watch -n 30 'brandgpt sessions list'
```

---

## Support and Contributing

- **Documentation**: [README.md](../README.md) - Main project documentation
- **Issues**: Report bugs and request features on GitHub
- **Examples**: Check the `examples/` directory for more usage patterns

The BrandGPT CLI provides a comprehensive interface to all BrandGPT API functionality with additional conveniences like configuration management, batch operations, and interactive modes.