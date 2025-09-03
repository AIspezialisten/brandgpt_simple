# BrandGPT Node.js Client Documentation

Welcome to the comprehensive documentation for the BrandGPT Node.js client library and CLI.

## 📚 Documentation Index

### Getting Started
- **[Main README](../README.md)** - Project overview, installation, and quick start
- **[API Library Usage](../README.md#quick-start)** - JavaScript/TypeScript client library examples
- **[CLI Quick Start](../README.md#cli-quick-start)** - Command-line interface basics

### CLI Documentation
- **[Complete CLI Guide](CLI.md)** - Comprehensive command reference and usage
- **[Interactive Tutorial](CLI-TUTORIAL.md)** - Step-by-step examples for real-world scenarios
- **[Man Page](brandgpt.1)** - Traditional Unix manual page

### API Reference
The library provides full TypeScript types and comprehensive error handling. Key areas:

- **Authentication** - JWT tokens and API key management
- **Sessions** - Document organization and management
- **Ingestion** - File upload, URL scraping, structured data
- **Querying** - RAG queries, search, and document analysis
- **Documents** - Document management and listing

## 🎯 Use Cases

### Research & Academia
- **Literature Review**: Analyze collections of research papers
- **Citation Analysis**: Find key references and relationships
- **Cross-paper Synthesis**: Generate comprehensive reviews

### Legal & Compliance
- **Contract Analysis**: Extract terms, clauses, and risks
- **Regulatory Compliance**: Check documents against requirements
- **Due Diligence**: Systematic document review processes

### Business Intelligence
- **Report Analysis**: Process internal reports and documentation
- **Knowledge Management**: Create searchable company knowledge bases
- **Policy Documentation**: Organize and query policy documents

### Customer Support
- **Knowledge Base Creation**: Build searchable support documentation
- **FAQ Generation**: Extract common questions and answers
- **Troubleshooting**: Interactive problem-solving assistance

### Content Analysis
- **Document Classification**: Categorize and organize large document sets
- **Sentiment Analysis**: Analyze customer feedback and reviews
- **Trend Identification**: Discover patterns across document collections

## 🛠️ Integration Examples

### CLI Integration
```bash
# Health monitoring
brandgpt health --server $SERVER_URL

# Automated processing pipeline
brandgpt ingest batch ./new-docs --session $SESSION_ID
brandgpt query batch questions.txt --session $SESSION_ID --output results.json

# Interactive workflows
brandgpt query chat --session $SESSION_ID
```

### JavaScript/Node.js Integration
```javascript
const { BrandGPTClient } = require('@marcapo/brandgpt-client');

const client = new BrandGPTClient({
  baseUrl: process.env.BRANDGPT_URL,
  apiKey: process.env.BRANDGPT_API_KEY
});

// Programmatic document processing
const session = await client.sessions.create({ name: 'Automated Analysis' });
const result = await client.query.query({
  query: 'Extract key insights',
  sessionId: session.id
});
```

### Shell Scripting
```bash
#!/bin/bash
# Daily report processing script

DATE=$(date +%Y-%m-%d)
SESSION_ID=$(brandgpt sessions create --name "Daily-$DATE" --format json | jq -r '.id')

# Process documents
for file in ./reports/*.pdf; do
  brandgpt ingest file "$file" --session $SESSION_ID
done

# Generate summary
brandgpt query ask "Summarize key findings from today's reports" \
  --session $SESSION_ID > "summary-$DATE.txt"
```

### Python Integration (via subprocess)
```python
import subprocess
import json

def brandgpt_query(session_id, question):
    """Query BrandGPT via CLI subprocess"""
    result = subprocess.run([
        'brandgpt', 'query', 'ask', question,
        '--session', session_id,
        '--format', 'json'
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        return json.loads(result.stdout)
    else:
        raise Exception(f"Query failed: {result.stderr}")

# Usage
response = brandgpt_query('session-id', 'What are the main topics?')
print(response['response'])
```

## 🔧 Development & Deployment

### Local Development
```bash
# Clone and setup
git clone https://github.com/marcapo/brandgpt-nodejs-client.git
cd brandgpt-nodejs-client
npm install
npm run build

# Test against local server
brandgpt health --server http://localhost:9700
```

### CI/CD Integration
```yaml
# GitHub Actions example
- name: Process Documents
  run: |
    npm install -g @marcapo/brandgpt-client
    brandgpt auth set-key --key ${{ secrets.BRANDGPT_API_KEY }}
    brandgpt ingest batch ./docs --session ${{ env.SESSION_ID }}
```

### Docker Integration
```dockerfile
FROM node:18
RUN npm install -g @marcapo/brandgpt-client
COPY scripts/ /scripts/
CMD ["./scripts/process-documents.sh"]
```

## 📊 Output Formats

### JSON Format
Perfect for programmatic processing and API integration:
```json
{
  "response": "The document discusses...",
  "sources": [
    {
      "text": "Relevant excerpt...",
      "score": 0.95,
      "filename": "document.pdf"
    }
  ]
}
```

### Table Format  
Human-readable output for terminal viewing:
```
┌─────────────┬──────────────────────────┐
│ Session ID  │ Name                     │
├─────────────┼──────────────────────────┤
│ ses_123     │ Research Project         │
│ ses_456     │ Legal Review             │
└─────────────┴──────────────────────────┘
```

### YAML Format
Configuration-friendly structured output:
```yaml
response: The document discusses machine learning applications...
sources:
  - text: Machine learning has transformed...
    score: 0.95
    filename: ml-paper.pdf
```

## 🐛 Troubleshooting

### Common Issues

#### Authentication Problems
- Use `brandgpt auth whoami` to check login status
- Verify API key format with `brandgpt config show`
- Test server connectivity with `brandgpt health --server URL`

#### File Processing Issues
- Check file permissions and paths
- Monitor processing with `brandgpt ingest status session-id`
- Use `--wait` flag for synchronous processing

#### Performance Optimization
- Use appropriate `--max-results` limits
- Implement batch processing for large document sets
- Use `--group-id` for content organization and filtering

### Debug Mode
Enable detailed logging for troubleshooting:
```bash
brandgpt --debug command...
```

### Configuration Reset
If configuration becomes corrupted:
```bash
brandgpt config clear
brandgpt auth login  # Re-authenticate
```

## 🤝 Support & Contributing

### Getting Help
- **GitHub Issues**: [Report bugs and request features](https://github.com/marcapo/brandgpt-nodejs-client/issues)
- **Documentation**: Browse these docs for detailed information
- **Built-in Help**: Use `brandgpt --help` and `brandgpt command --help`

### Contributing
- Fork the repository
- Create feature branches
- Submit pull requests with tests
- Update documentation for new features

### Development Setup
```bash
git clone https://github.com/marcapo/brandgpt-nodejs-client.git
cd brandgpt-nodejs-client
npm install
npm run build
npm test
```

---

**Next Steps**: Start with the [CLI Tutorial](CLI-TUTORIAL.md) for hands-on examples, or dive into the [Complete CLI Guide](CLI.md) for comprehensive command reference.