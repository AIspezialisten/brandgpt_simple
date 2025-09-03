# BrandGPT CLI Workflow Diagram

This document illustrates the necessary workflow for using the BrandGPT CLI effectively.

## 📊 Complete Workflow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          BRANDGPT CLI WORKFLOW                                 │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐
│   1. SETUP      │
└─────┬───────────┘
      │
      ▼
┌─────────────────────────────────────┐      ┌─────────────────────────────────┐
│ Install CLI                         │      │ Check Server Health             │
│ npm install -g @marcapo/brandgpt... │ ──── │ brandgpt health --server <url>  │
└─────────────────────────────────────┘      └─────────────┬───────────────────┘
                                                           │
                                                           ▼
┌─────────────────┐                                     ┌─────────────────────────────────┐
│ 2. AUTHENTICATE │ ◄───────────────────────────────────│ Configure Base URL (Optional)  │
└─────┬───────────┘                                     │ brandgpt config set baseUrl... │
      │                                                 └─────────────────────────────────┘
      ▼
┌─────────────────────────────────────┐      ┌─────────────────────────────────┐
│ Login/Register                      │      │ Or Set API Key Directly         │
│ brandgpt auth login                 │ ──── │ brandgpt auth set-key --key...  │
│ brandgpt auth register              │      └─────────────────────────────────┘
└─────────────┬───────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│ Verify Authentication               │
│ brandgpt auth whoami                │
└─────────────┬───────────────────────┘
              │
              ▼
┌─────────────────┐
│ 3. SESSION      │
└─────┬───────────┘
      │
      ▼
┌─────────────────────────────────────┐      ┌─────────────────────────────────┐
│ Create Session                      │      │ Or Use Existing Session        │
│ brandgpt sessions create            │ ──── │ brandgpt sessions list          │
│   --name "Project Name"             │      │ brandgpt sessions get <id>      │
└─────────────┬───────────────────────┘      └─────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│ Save Session ID                     │
│ SESSION_ID="49e3a571-bb91..."       │
└─────────────┬───────────────────────┘
              │
              ▼
┌─────────────────┐
│ 4. INGEST DATA  │
└─────┬───────────┘
      │
      ▼
┌─────────────────────────────────────┐
│        INGESTION OPTIONS            │
├─────────────────────────────────────┤
│ Single File:                        │
│ brandgpt ingest file doc.pdf        │
│   --session $SESSION_ID             │
│   --group-id "category"             │
│                                     │
│ Batch Upload:                       │
│ brandgpt ingest batch ./docs        │
│   --session $SESSION_ID             │
│   --pattern "*.pdf"                 │
│   --recursive                       │
│                                     │
│ URL Scraping:                       │
│ brandgpt ingest url https://...     │
│   --session $SESSION_ID             │
│   --depth 2                         │
│                                     │
│ Structured Data:                    │
│ brandgpt ingest data data.json      │
│   --session $SESSION_ID             │
└─────────────┬───────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│ Monitor Processing Status           │
│ brandgpt ingest status $SESSION_ID  │
│ (Wait until all docs processed)     │
└─────────────┬───────────────────────┘
              │
              ▼
┌─────────────────┐
│ 5. QUERY & USE  │
└─────┬───────────┘
      │
      ▼
┌─────────────────────────────────────┐
│           QUERY OPTIONS             │
├─────────────────────────────────────┤
│ Interactive Q&A:                    │
│ brandgpt query ask "Question?"      │
│   --session $SESSION_ID             │
│                                     │
│ Chat Mode:                          │
│ brandgpt query chat                 │
│   --session $SESSION_ID             │
│                                     │
│ Search Terms:                       │
│ brandgpt query search "keywords"    │
│   --session $SESSION_ID             │
│   --threshold 0.8                   │
│                                     │
│ Batch Queries:                      │
│ brandgpt query batch questions.txt  │
│   --session $SESSION_ID             │
│   --output results.json             │
└─────────────┬───────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│ Process Results                     │
│ • View formatted output             │
│ • Export to JSON/YAML               │
│ • Pipe to other tools               │
│ • Generate reports                  │
└─────────────────────────────────────┘
```

## 🔄 Decision Tree Workflow

```
START
  │
  ├─ First Time User?
  │  ├─ YES → Install CLI → Health Check → Register/Login
  │  └─ NO → Login Check (whoami)
  │
  ├─ Need New Session?
  │  ├─ YES → Create Session → Save Session ID
  │  └─ NO → List Sessions → Select Session ID
  │
  ├─ Have Documents to Process?
  │  ├─ YES → Choose Ingestion Method:
  │  │       ├─ Single File → ingest file
  │  │       ├─ Multiple Files → ingest batch  
  │  │       ├─ Web Content → ingest url
  │  │       └─ JSON Data → ingest data
  │  │       └─ Monitor → ingest status
  │  └─ NO → Skip to Querying
  │
  ├─ Ready to Query?
  │  ├─ Simple Question → query ask
  │  ├─ Interactive Session → query chat
  │  ├─ Search Specific Terms → query search
  │  └─ Multiple Questions → query batch
  │
  └─ Process Results → Export/Report → END
```

## 📋 Workflow Steps Breakdown

### Phase 1: Environment Setup

```bash
# 1.1 Installation
npm install -g @marcapo/brandgpt-client

# 1.2 Health Check
brandgpt health --server https://your-server.com

# 1.3 Configuration (Optional)
brandgpt config set baseUrl "https://your-server.com"
brandgpt config show
```

**Decision Point**: ✅ Server accessible?  
- **YES**: Proceed to authentication
- **NO**: Fix server connectivity issues

### Phase 2: Authentication

```bash
# Option A: New User Registration
brandgpt auth register
# Interactive prompts for: username, email, password, server
# Auto-login and API key generation offered

# Option B: Existing User Login  
brandgpt auth login
# Interactive prompts for: username, password
# API key generation offered

# Option C: Direct API Key
brandgpt auth set-key --key "bgpt_your_api_key"

# Verification
brandgpt auth whoami
```

**Decision Point**: ✅ Authenticated successfully?
- **YES**: Proceed to session management
- **NO**: Check credentials, server URL, network connectivity

### Phase 3: Session Management

```bash
# Option A: Create New Session
brandgpt sessions create --name "Project Description $(date +%Y-%m-%d)"
# Save the returned session ID

# Option B: Use Existing Session
brandgpt sessions list --format table
# Copy desired session ID

# Session Validation
brandgpt sessions get $SESSION_ID
```

**Decision Point**: ✅ Session ready?
- **YES**: Proceed to data ingestion
- **NO**: Create new session or check session permissions

### Phase 4: Data Ingestion

#### Single File Upload
```bash
brandgpt ingest file document.pdf \
  --session $SESSION_ID \
  --group-id "category-name" \
  --wait
```

#### Batch File Processing
```bash
# Upload all PDFs from directory
brandgpt ingest batch ./documents \
  --session $SESSION_ID \
  --pattern "*.pdf" \
  --recursive \
  --group-id "batch-docs"
```

#### URL Scraping
```bash
brandgpt ingest url "https://documentation-site.com" \
  --session $SESSION_ID \
  --depth 3 \
  --group-id "web-content" \
  --wait
```

#### Structured Data
```bash
# From file
brandgpt ingest data metadata.json \
  --session $SESSION_ID \
  --group-id "structured"

# From stdin
echo '{"key": "value"}' | brandgpt ingest data --stdin \
  --session $SESSION_ID
```

#### Processing Monitoring
```bash
# Check status until all processed
brandgpt ingest status $SESSION_ID

# Or use --wait flag for automatic waiting
```

**Decision Point**: ✅ All documents processed?
- **YES**: Proceed to querying
- **NO**: Wait for processing or check for errors

### Phase 5: Querying & Analysis

#### Interactive Question-Answer
```bash
brandgpt query ask "What are the main themes in these documents?" \
  --session $SESSION_ID \
  --max-results 5 \
  --format table
```

#### Chat Mode
```bash
brandgpt query chat --session $SESSION_ID
# Interactive conversation:
# > What is the executive summary?
# > What risks are mentioned?
# > exit
```

#### Specific Term Search
```bash
brandgpt query search "compliance requirements" \
  --session $SESSION_ID \
  --threshold 0.85 \
  --group-id "legal-docs"
```

#### Batch Query Processing
```bash
# Create questions file
echo "What are the key findings?
What methodology was used?
What are the recommendations?
What are the limitations?" > analysis-questions.txt

# Process all questions
brandgpt query batch analysis-questions.txt \
  --session $SESSION_ID \
  --output detailed-analysis.json \
  --delay 2000
```

**Decision Point**: ✅ Results satisfactory?
- **YES**: Proceed to results processing
- **NO**: Refine questions, adjust parameters, add more documents

### Phase 6: Results Processing & Export

#### Format Conversion
```bash
# Extract just answers
jq -r '.[] | "\(.question)\n\(.response)\n---"' results.json > report.txt

# Create structured report
brandgpt query ask "Executive summary" --session $SESSION_ID --format yaml > summary.yaml
```

#### Integration with Other Tools
```bash
# Pipe to analysis tools
brandgpt sessions list --format json | jq '.[] | .id' | head -5

# Export for spreadsheet analysis
brandgpt query batch questions.txt --session $SESSION_ID --format json | \
  jq -r '.[] | [.question, .response] | @csv' > analysis.csv
```

## 🔄 Common Usage Patterns

### Pattern 1: Research Paper Analysis
```bash
# Setup
SESSION_ID=$(brandgpt sessions create --name "Research-$(date +%Y%m%d)" --format json | jq -r '.id')

# Ingest papers with organization
brandgpt ingest file paper1.pdf --session $SESSION_ID --group-id "ai-research"
brandgpt ingest file paper2.pdf --session $SESSION_ID --group-id "ml-research"

# Comprehensive analysis
echo "What are the main contributions?
How do the methodologies differ?
What future work is suggested?" > research-questions.txt

brandgpt query batch research-questions.txt --session $SESSION_ID --output research-analysis.json
```

### Pattern 2: Legal Document Review
```bash
# Batch processing
brandgpt ingest batch ./contracts --session $SESSION_ID --pattern "*.pdf" --wait

# Risk assessment
brandgpt query ask "What are the key risks across all contracts?" --session $SESSION_ID
brandgpt query search "indemnification" --session $SESSION_ID --threshold 0.9
```

### Pattern 3: Interactive Support Knowledge Base
```bash
# Build knowledge base
brandgpt ingest url "https://docs.company.com" --session $SESSION_ID --depth 2
brandgpt ingest batch ./support-docs --session $SESSION_ID

# Interactive support
brandgpt query chat --session $SESSION_ID
```

## ⚡ Workflow Optimization Tips

### 1. Efficient Session Management
- Use descriptive session names with dates
- Organize content with meaningful group IDs
- Reuse sessions for related documents

### 2. Batch Processing Strategies
- Use `--wait` for critical uploads only
- Monitor processing with `ingest status`
- Group similar documents with consistent group IDs

### 3. Query Optimization
- Start with broad questions, then narrow down
- Use appropriate `--max-results` limits
- Leverage `--threshold` for search precision

### 4. Output Management
- Use `--format json` for programmatic processing
- Use `--output` for batch results
- Pipe results to analysis tools

### 5. Error Prevention
- Always verify authentication before batch operations
- Check processing status before querying
- Use health checks to validate server connectivity

## 🔧 Automation Script Template

```bash
#!/bin/bash
# BrandGPT CLI Automation Template

set -e  # Exit on any error

# Configuration
SERVER_URL="https://your-server.com"
PROJECT_NAME="Automated-Analysis-$(date +%Y%m%d)"
DOCS_DIR="./documents"
QUESTIONS_FILE="./questions.txt"
OUTPUT_DIR="./results"

# 1. Health Check
echo "Checking server health..."
brandgpt health --server "$SERVER_URL"

# 2. Authentication Check
echo "Verifying authentication..."
brandgpt auth whoami > /dev/null

# 3. Create Session
echo "Creating session: $PROJECT_NAME"
SESSION_ID=$(brandgpt sessions create --name "$PROJECT_NAME" --format json | jq -r '.id')
echo "Session ID: $SESSION_ID"

# 4. Batch Upload
echo "Uploading documents from $DOCS_DIR..."
brandgpt ingest batch "$DOCS_DIR" --session "$SESSION_ID" --pattern "*.pdf" --wait

# 5. Verify Processing
echo "Checking processing status..."
brandgpt ingest status "$SESSION_ID"

# 6. Run Analysis
echo "Running batch queries..."
mkdir -p "$OUTPUT_DIR"
brandgpt query batch "$QUESTIONS_FILE" \
  --session "$SESSION_ID" \
  --output "$OUTPUT_DIR/analysis-$(date +%Y%m%d).json"

# 7. Generate Summary
echo "Generating executive summary..."
brandgpt query ask "Provide an executive summary of all documents" \
  --session "$SESSION_ID" \
  --format yaml > "$OUTPUT_DIR/summary-$(date +%Y%m%d).yaml"

echo "Analysis complete! Results in $OUTPUT_DIR"
echo "Session ID for future reference: $SESSION_ID"
```

## 📈 Workflow Success Metrics

### Performance Benchmarks
- **Setup Time**: < 2 minutes for new users
- **Authentication**: < 30 seconds
- **File Upload**: ~1-3 seconds per MB
- **Processing**: ~2-5 seconds per document
- **Query Response**: ~5-15 seconds depending on complexity

### Quality Indicators
- ✅ All documents show "Yes" in processing status
- ✅ Queries return relevant sources
- ✅ Answers directly address questions
- ✅ Error messages are clear and actionable

This workflow ensures reliable, efficient use of the BrandGPT CLI for any document analysis scenario.