# BrandGPT CLI Quick Reference

A condensed reference for the most commonly used BrandGPT CLI commands.

## Installation & Setup

```bash
npm install -g @marcapo/brandgpt-client  # Install CLI globally
brandgpt --help                          # Show help
brandgpt --version                       # Show version
brandgpt health --server <url>           # Test server connectivity
```

## Authentication

```bash
brandgpt auth login                       # Login interactively
brandgpt auth register                   # Register new account
brandgpt auth set-key --key <api-key>    # Set API key manually
brandgpt auth whoami                     # Show current user
brandgpt auth logout                     # Clear credentials
```

## Session Management

```bash
brandgpt sessions list                   # List all sessions
brandgpt sessions create -n "Name"       # Create new session
brandgpt sessions get <session-id>       # Get session details
brandgpt sessions delete <session-id>    # Delete session
brandgpt sessions docs <session-id>      # List session documents
```

## Document Ingestion

```bash
# Single file upload
brandgpt ingest file doc.pdf -s <session-id>

# Batch upload from directory  
brandgpt ingest batch ./docs -s <session-id> --pattern "*.pdf"

# URL scraping
brandgpt ingest url https://example.com -s <session-id> --depth 2

# JSON data ingestion
brandgpt ingest data data.json -s <session-id>

# Check processing status
brandgpt ingest status <session-id>
```

## Querying & Search

```bash
# Ask questions
brandgpt query ask "What are the key findings?" -s <session-id>

# Interactive chat
brandgpt query chat -s <session-id>

# Search for terms
brandgpt query search "machine learning" -s <session-id>

# Batch queries from file
brandgpt query batch questions.txt -s <session-id> --output results.json
```

## Configuration

```bash
brandgpt config show                     # Show current config
brandgpt config set baseUrl <url>        # Set server URL
brandgpt config clear                    # Reset configuration
brandgpt --config-path                   # Show config file location
```

## Common Options

| Option | Description | Example |
|--------|-------------|---------|
| `--session -s` | Session ID (required for most commands) | `-s session-123` |
| `--group-id -g` | Group ID for organization | `-g "legal-docs"` |
| `--format` | Output format (json/table/yaml) | `--format json` |
| `--max-results -m` | Limit number of results | `-m 10` |
| `--wait` | Wait for processing to complete | `--wait` |
| `--debug` | Enable debug output | `--debug` |

## Output Formats

```bash
# Table format (default, human-readable)
brandgpt sessions list --format table

# JSON format (machine-readable)
brandgpt sessions list --format json

# YAML format (configuration-friendly)
brandgpt sessions list --format yaml
```

## Common Workflows

### Quick Document Analysis

```bash
# 1. Setup
brandgpt auth login
SESSION_ID=$(brandgpt sessions create -n "Analysis" --format json | jq -r '.id')

# 2. Upload documents
brandgpt ingest file document.pdf -s $SESSION_ID

# 3. Ask questions
brandgpt query ask "Summarize this document" -s $SESSION_ID
```

### Batch Processing Pipeline

```bash
# Upload multiple files
brandgpt ingest batch ./documents -s $SESSION_ID --pattern "*.pdf" --wait

# Run multiple queries
echo "What are the main topics?
What are the key findings?
What are the recommendations?" > questions.txt

brandgpt query batch questions.txt -s $SESSION_ID --output analysis.json
```

### Interactive Research Session

```bash
# Setup session with organized content
brandgpt ingest file paper1.pdf -s $SESSION_ID --group-id "ai"
brandgpt ingest file paper2.pdf -s $SESSION_ID --group-id "ml"

# Interactive exploration
brandgpt query chat -s $SESSION_ID
# > What are the AI developments mentioned?
# > How do the ML approaches differ?
# > exit
```

## Error Handling

```bash
# Check authentication status
brandgpt auth whoami

# Test server connection
brandgpt health --server https://api.brandgpt.com

# Monitor document processing
brandgpt ingest status <session-id>

# Enable debug mode for troubleshooting
brandgpt --debug command...
```

## Scripting Examples

### Shell Script Integration

```bash
#!/bin/bash
# Process daily reports

DATE=$(date +%Y-%m-%d)
SESSION_ID=$(brandgpt sessions create -n "Reports-$DATE" --format json | jq -r '.id')

# Upload reports
brandgpt ingest batch ./reports -s $SESSION_ID --pattern "*.pdf"

# Generate summary
brandgpt query ask "Provide executive summary" -s $SESSION_ID > "summary-$DATE.txt"

echo "Processing complete. Session: $SESSION_ID"
```

### JSON Processing with jq

```bash
# Extract specific fields
brandgpt query ask "Summary" -s $SESSION_ID --format json | jq -r '.response'

# Get session IDs
brandgpt sessions list --format json | jq -r '.[].id'

# Process batch results
brandgpt query batch questions.txt -s $SESSION_ID --format json | \
  jq -r '.[] | "\(.question): \(.response)"'
```

## Tips & Best Practices

1. **Use descriptive session names** with dates: `"Legal-Review-2024-01-15"`
2. **Organize with group IDs**: `--group-id "contracts"`, `--group-id "policies"`
3. **Save important session IDs**: Store in environment variables or files
4. **Monitor processing**: Use `--wait` for critical uploads
5. **Batch operations**: More efficient for multiple files/queries
6. **Format appropriately**: `--format json` for scripts, `table` for humans
7. **Use configuration**: Set common values in config to avoid repetition

## Help & Documentation

```bash
brandgpt --help                    # Main help
brandgpt auth --help               # Authentication help
brandgpt query ask --help          # Specific command help
```

**Full Documentation**: See `docs/CLI.md` for comprehensive guide and `docs/CLI-TUTORIAL.md` for detailed examples.

---

*Quick Reference v1.0 - BrandGPT CLI*