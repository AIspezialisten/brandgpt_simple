# BrandGPT CLI Tutorial

This tutorial walks you through practical examples of using the BrandGPT CLI for real-world document analysis and RAG applications.

## Prerequisites

- BrandGPT server running (local or remote)
- Node.js 16+ installed
- CLI installed: `npm install -g @marcapo/brandgpt-client`

## Tutorial 1: Research Paper Analysis

Let's analyze a collection of research papers to extract key insights.

### Step 1: Setup and Authentication

```bash
# Check server connectivity
brandgpt health --server http://localhost:9700

# Register or login
brandgpt auth login
# Enter your credentials when prompted
```

### Step 2: Create a Research Session

```bash
# Create a dedicated session for research
brandgpt sessions create --name "AI Research Analysis 2024"

# Save the session ID for later use
SESSION_ID="your-session-id-here"  # Copy from the output above
```

### Step 3: Upload Research Papers

```bash
# Upload individual papers
brandgpt ingest file "paper1-transformers.pdf" --session $SESSION_ID --group-id "nlp"
brandgpt ingest file "paper2-vision.pdf" --session $SESSION_ID --group-id "cv"

# Batch upload from a directory
brandgpt ingest batch "./research-papers" --session $SESSION_ID --pattern "*.pdf" --recursive

# Check processing status
brandgpt ingest status $SESSION_ID
```

### Step 4: Analyze the Papers

```bash
# Get overall summary
brandgpt query ask "What are the main research topics covered in these papers?" --session $SESSION_ID

# Focus on specific areas
brandgpt query ask "What are the latest developments in transformer architecture?" --session $SESSION_ID --group-id "nlp"

# Search for specific concepts
brandgpt query search "attention mechanism" --session $SESSION_ID --max-results 5
```

### Step 5: Generate Research Report

```bash
# Create comprehensive questions
cat > research_questions.txt << EOF
What are the key methodological innovations across these papers?
What datasets and evaluation metrics are commonly used?
What are the main limitations identified by the authors?
What future research directions are suggested?
How do these papers build upon previous work?
EOF

# Run batch analysis
brandgpt query batch research_questions.txt --session $SESSION_ID --output research_analysis.json

# Extract insights
jq -r '.[] | "\(.question)\n\(.response)\n---"' research_analysis.json > research_report.md
```

## Tutorial 2: Company Documentation Analysis

Analyze internal company documents to create a knowledge base.

### Step 1: Setup Documentation Session

```bash
# Create session for company docs
brandgpt sessions create --name "Company Knowledge Base"
DOCS_SESSION="your-docs-session-id"
```

### Step 2: Organize Documents by Department

```bash
# Upload HR documents
brandgpt ingest batch "./hr-docs" --session $DOCS_SESSION --group-id "hr" --pattern "*.{pdf,docx,md}"

# Upload technical documentation
brandgpt ingest batch "./tech-specs" --session $DOCS_SESSION --group-id "technical" --pattern "*.{md,txt,pdf}"

# Upload policies and procedures
brandgpt ingest batch "./policies" --session $DOCS_SESSION --group-id "policies" --pattern "*.pdf"

# Add structured data (employee handbook)
cat > employee_data.json << EOF
{
  "company": "TechCorp",
  "policies": {
    "remote_work": "Allowed 3 days per week",
    "vacation": "25 days annually",
    "benefits": ["Health insurance", "401k", "Stock options"]
  },
  "departments": ["Engineering", "Sales", "Marketing", "HR"],
  "contact_info": {
    "hr": "hr@techcorp.com",
    "it": "it@techcorp.com"
  }
}
EOF

brandgpt ingest data employee_data.json --session $DOCS_SESSION --group-id "hr"
```

### Step 3: Create Department-Specific Queries

```bash
# HR queries
brandgpt query ask "What is the remote work policy?" --session $DOCS_SESSION --group-id "hr"
brandgpt query ask "How many vacation days do employees get?" --session $DOCS_SESSION --group-id "hr"

# Technical queries  
brandgpt query ask "What are the system requirements for our main product?" --session $DOCS_SESSION --group-id "technical"

# Cross-department queries
brandgpt query ask "What are the security protocols across all departments?" --session $DOCS_SESSION
```

### Step 4: Interactive Help Desk

```bash
# Start chat mode for interactive Q&A
brandgpt query chat --session $DOCS_SESSION

# Example interaction:
# > What are the steps to report a security incident?
# > How do I request time off?  
# > What software licenses does the company have?
# > exit
```

## Tutorial 3: Legal Document Analysis

Process and analyze legal contracts and agreements.

### Step 1: Setup Legal Analysis

```bash
# Create secure session for legal docs
brandgpt sessions create --name "Contract Analysis - Q4 2024"
LEGAL_SESSION="your-legal-session-id"
```

### Step 2: Process Different Contract Types

```bash
# Organize contracts by type
brandgpt ingest file "vendor-agreement-acme.pdf" --session $LEGAL_SESSION --group-id "vendor-contracts"
brandgpt ingest file "employment-contract-template.pdf" --session $LEGAL_SESSION --group-id "employment"
brandgpt ingest file "nda-standard.pdf" --session $LEGAL_SESSION --group-id "nda"

# Wait for processing to complete
brandgpt ingest status $LEGAL_SESSION --format table
```

### Step 3: Extract Key Legal Information

```bash
# Create legal analysis questions
cat > legal_questions.txt << EOF
What are the key terms and conditions in the vendor contracts?
What are the termination clauses across all agreements?
What intellectual property rights are mentioned?
What are the liability limitations?
What are the governing law and jurisdiction clauses?
Are there any unusual or non-standard terms?
EOF

# Analyze contracts
brandgpt query batch legal_questions.txt --session $LEGAL_SESSION --output legal_analysis.json --delay 2000

# Generate summary report
echo "# Legal Document Analysis Report" > legal_report.md
echo "Generated: $(date)" >> legal_report.md
echo "" >> legal_report.md

jq -r '.[] | "## \(.question)\n\n\(.response)\n"' legal_analysis.json >> legal_report.md
```

### Step 4: Risk Assessment

```bash
# Specific risk-focused queries
brandgpt query ask "What potential risks or red flags should we be aware of in these contracts?" --session $LEGAL_SESSION

# Compliance check
brandgpt query ask "Are there any clauses that might conflict with our standard terms?" --session $LEGAL_SESSION

# Search for specific terms
brandgpt query search "indemnification" --session $LEGAL_SESSION --threshold 0.85
brandgpt query search "force majeure" --session $LEGAL_SESSION
```

## Tutorial 4: Customer Support Knowledge Base

Build a searchable knowledge base from support documentation.

### Step 1: Setup Support KB

```bash
# Create support session
brandgpt sessions create --name "Customer Support Knowledge Base"
SUPPORT_SESSION="your-support-session-id"
```

### Step 2: Ingest Multi-format Documentation

```bash
# Add FAQ from web
brandgpt ingest url "https://yourcompany.com/faq" --session $SUPPORT_SESSION --group-id "faq" --depth 2

# Add troubleshooting guides  
brandgpt ingest batch "./troubleshooting" --session $SUPPORT_SESSION --group-id "troubleshooting"

# Add product documentation
brandgpt ingest batch "./product-docs" --session $SUPPORT_SESSION --group-id "product-info"

# Add structured support data
cat > support_data.json << EOF
{
  "common_issues": [
    {
      "issue": "Login problems",
      "solution": "Clear browser cache and cookies",
      "category": "authentication"
    },
    {
      "issue": "Payment processing",
      "solution": "Verify billing information and try different card",
      "category": "billing"
    }
  ],
  "escalation_procedures": {
    "level_1": "Technical support team",
    "level_2": "Senior engineer",
    "level_3": "Development team lead"
  },
  "contact_info": {
    "support_email": "support@company.com",
    "emergency": "emergency@company.com"
  }
}
EOF

brandgpt ingest data support_data.json --session $SUPPORT_SESSION --group-id "procedures"
```

### Step 3: Test Support Queries

```bash
# Common customer questions
brandgpt query ask "How do I reset my password?" --session $SUPPORT_SESSION
brandgpt query ask "Why is my payment being declined?" --session $SUPPORT_SESSION
brandgpt query ask "How do I cancel my subscription?" --session $SUPPORT_SESSION

# Technical troubleshooting
brandgpt query search "error 500" --session $SUPPORT_SESSION
brandgpt query search "connection timeout" --session $SUPPORT_SESSION
```

### Step 4: Support Agent Training

```bash
# Create training scenarios
cat > support_scenarios.txt << EOF
A customer reports they cannot access their account after recent update
A customer's payment was charged twice this month
A customer wants to downgrade their plan but keep their data
A customer reports slow performance during peak hours
A customer needs help integrating our API with their system
EOF

# Generate responses for training
brandgpt query batch support_scenarios.txt --session $SUPPORT_SESSION --output training_responses.json

# Interactive training session
echo "Starting support training simulation..."
brandgpt query chat --session $SUPPORT_SESSION
```

## Tutorial 5: Academic Research Workflow

Comprehensive workflow for academic research and literature review.

### Step 1: Literature Collection

```bash
# Create research session
brandgpt sessions create --name "Climate Change Research Literature Review"
RESEARCH_SESSION="your-research-session-id"

# Add papers by topic
brandgpt ingest batch "./papers/climate-modeling" --session $RESEARCH_SESSION --group-id "modeling" --wait
brandgpt ingest batch "./papers/policy-analysis" --session $RESEARCH_SESSION --group-id "policy" --wait
brandgpt ingest batch "./papers/impact-studies" --session $RESEARCH_SESSION --group-id "impacts" --wait

# Add supplementary materials
brandgpt ingest url "https://ipcc.ch/reports" --session $RESEARCH_SESSION --group-id "reports" --depth 2
```

### Step 2: Systematic Analysis

```bash
# Research methodology analysis
brandgpt query ask "What research methodologies are most commonly used across these papers?" --session $RESEARCH_SESSION

# Compare findings by group
brandgpt query ask "How do climate models compare in their predictions?" --session $RESEARCH_SESSION --group-id "modeling"
brandgpt query ask "What policy interventions show the most promise?" --session $RESEARCH_SESSION --group-id "policy"

# Identify research gaps
brandgpt query ask "What are the main research gaps identified across this literature?" --session $RESEARCH_SESSION
```

### Step 3: Citation and Reference Analysis

```bash
# Find key references
brandgpt query search "Hansen et al" --session $RESEARCH_SESSION
brandgpt query search "IPCC AR6" --session $RESEARCH_SESSION

# Generate bibliography questions
cat > bibliography_questions.txt << EOF
What are the most frequently cited papers in this collection?
Which authors appear most often across these studies?
What are the key foundational papers that most studies reference?
Are there any recent breakthrough papers that change the field?
EOF

brandgpt query batch bibliography_questions.txt --session $RESEARCH_SESSION --output bibliography_analysis.json
```

### Step 4: Research Synthesis

```bash
# Generate comprehensive literature review
brandgpt query ask "Provide a comprehensive synthesis of the current state of climate change research based on these papers, including key findings, methodologies, and future directions" --session $RESEARCH_SESSION --max-results 15 > literature_review.txt

# Create research outline
cat > outline_questions.txt << EOF
What are the main themes that emerge from this literature?
How has the field evolved over time based on these papers?  
What are the most significant controversies or debates?
What practical applications emerge from this research?
EOF

brandgpt query batch outline_questions.txt --session $RESEARCH_SESSION --output research_outline.json
```

## Tutorial 6: Multi-language Document Processing

Handle documents in multiple languages and formats.

### Step 1: International Business Analysis

```bash
# Create multilingual session
brandgpt sessions create --name "Global Market Analysis"
GLOBAL_SESSION="your-global-session-id"

# Upload documents by region
brandgpt ingest file "market-report-en.pdf" --session $GLOBAL_SESSION --group-id "english"
brandgpt ingest file "informe-mercado-es.pdf" --session $GLOBAL_SESSION --group-id "spanish"  
brandgpt ingest file "rapport-marché-fr.pdf" --session $GLOBAL_SESSION --group-id "french"
```

### Step 2: Cross-language Analysis

```bash
# Analyze across languages
brandgpt query ask "What are the common market trends identified across all regional reports?" --session $GLOBAL_SESSION

# Language-specific insights
brandgpt query ask "What specific challenges are mentioned in the Spanish market report?" --session $GLOBAL_SESSION --group-id "spanish"

# Comparative analysis
brandgpt query ask "How do the market conditions differ between European and Latin American markets?" --session $GLOBAL_SESSION
```

## Best Practices and Tips

### 1. Session Organization

```bash
# Use descriptive session names with dates
brandgpt sessions create --name "Q4-2024-Legal-Contract-Review"
brandgpt sessions create --name "Product-Launch-Documentation-$(date +%Y-%m-%d)"

# List and clean up old sessions
brandgpt sessions list
brandgpt sessions delete old-session-id
```

### 2. Effective Group Usage

```bash
# Organize by document type
--group-id "contracts"
--group-id "policies"  
--group-id "technical-docs"

# Organize by department
--group-id "hr"
--group-id "engineering"
--group-id "legal"

# Organize by project
--group-id "project-alpha"
--group-id "compliance-audit"
```

### 3. Query Optimization

```bash
# Use specific, focused questions
brandgpt query ask "What are the specific liability clauses in vendor contracts?" --session $SESSION_ID

# Rather than broad questions
brandgpt query ask "Tell me about the contracts" --session $SESSION_ID

# Use appropriate max-results
--max-results 3    # For quick overview
--max-results 10   # For comprehensive analysis
--max-results 1    # For finding specific information
```

### 4. Batch Processing Efficiency

```bash
# Process large document sets in groups
brandgpt ingest batch "./docs/batch1" --session $SESSION_ID --pattern "*.pdf"
sleep 60  # Allow processing time
brandgpt ingest batch "./docs/batch2" --session $SESSION_ID --pattern "*.pdf"

# Use appropriate delays for batch queries
brandgpt query batch questions.txt --session $SESSION_ID --delay 2000  # 2 second delay
```

### 5. Output Management

```bash
# Save important results
brandgpt query ask "Executive summary" --session $SESSION_ID --format json > summary.json
brandgpt query ask "Executive summary" --session $SESSION_ID --format yaml > summary.yaml

# Create formatted reports
brandgpt query ask "Detailed analysis" --session $SESSION_ID | tee analysis_report.txt
```

### 6. Monitoring and Maintenance

```bash
# Regular status checks
brandgpt ingest status $SESSION_ID

# Monitor authentication
brandgpt auth whoami

# Clean up completed sessions
brandgpt sessions list --format json | jq -r '.[] | select(.name | contains("temp")) | .id' | xargs -I {} brandgpt sessions delete {} --force
```

## Troubleshooting Common Issues

### Processing Delays

```bash
# Check processing status regularly
watch -n 10 'brandgpt ingest status session-id'

# Use --wait for important uploads
brandgpt ingest file important-doc.pdf --session $SESSION_ID --wait
```

### Large Document Sets

```bash
# Process in smaller batches
find ./large-doc-set -name "*.pdf" | head -10 | xargs -I {} brandgpt ingest file {} --session $SESSION_ID

# Monitor system resources
brandgpt health --server $SERVER_URL
```

### Query Optimization

```bash
# If getting too many irrelevant results
brandgpt query search "specific term" --session $SESSION_ID --threshold 0.9

# If getting too few results  
brandgpt query search "broader term" --session $SESSION_ID --threshold 0.6 --max-results 15
```

This tutorial provides practical, real-world examples of using the BrandGPT CLI for various document analysis scenarios. Each tutorial builds on core concepts while demonstrating advanced features and best practices.