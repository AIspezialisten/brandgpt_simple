# BrandGPT Node.js Client - Developer Guide

A comprehensive guide for developers using the BrandGPT Node.js client library for building RAG (Retrieval-Augmented Generation) applications.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Authentication](#authentication)
3. [Session Management](#session-management)
4. [Content Ingestion](#content-ingestion)
5. [Querying and Retrieval](#querying-and-retrieval)
6. [Advanced Usage Patterns](#advanced-usage-patterns)
7. [Error Handling](#error-handling)
8. [Performance Optimization](#performance-optimization)
9. [Best Practices](#best-practices)
10. [Real-World Examples](#real-world-examples)

---

## Getting Started

### Installation and Setup

```bash
npm install @marcapo/brandgpt-client
```

### Basic Client Initialization

```typescript
import { BrandGPTClient } from '@marcapo/brandgpt-client';

const client = new BrandGPTClient({
  baseUrl: 'https://api.brandgpt.com',
  apiKey: 'your-api-key-here',
  timeout: 30000 // Optional: 30 second timeout
});
```

### Environment-Based Configuration

```typescript
// config/brandgpt.ts
export const createBrandGPTClient = () => {
  const config = {
    baseUrl: process.env.BRANDGPT_BASE_URL || 'https://api.brandgpt.com',
    apiKey: process.env.BRANDGPT_API_KEY,
    timeout: parseInt(process.env.BRANDGPT_TIMEOUT || '30000')
  };

  if (!config.apiKey) {
    throw new Error('BRANDGPT_API_KEY environment variable is required');
  }

  return new BrandGPTClient(config);
};

// Usage
const client = createBrandGPTClient();
```

---

## Authentication

### API Key Authentication (Recommended)

```typescript
// Option 1: Initialize with API key
const client = new BrandGPTClient({
  baseUrl: 'https://api.brandgpt.com',
  apiKey: 'bgpt_your_api_key_here'
});

// Option 2: Set API key after initialization
const client = new BrandGPTClient({ baseUrl: 'https://api.brandgpt.com' });
client.setApiKey('bgpt_your_api_key_here');
```

### JWT Token Authentication

```typescript
// Login with username/password to get JWT token
const loginClient = new BrandGPTClient({ baseUrl: 'https://api.brandgpt.com' });

const tokenResponse = await loginClient.auth.login({
  username: 'your_username',
  password: 'your_password'
});

// Use JWT token for subsequent requests
const authenticatedClient = new BrandGPTClient({
  baseUrl: 'https://api.brandgpt.com',
  apiKey: tokenResponse.access_token
});
```

### User Registration and API Key Generation

```typescript
class AuthenticationManager {
  private client: BrandGPTClient;

  constructor(baseUrl: string) {
    this.client = new BrandGPTClient({ baseUrl });
  }

  async registerAndSetupUser(userData: {
    username: string;
    email: string;
    password: string;
  }) {
    try {
      // Register new user
      const user = await this.client.auth.register(userData);
      console.log('User registered:', user);

      // Login to get JWT token
      const tokenResponse = await this.client.auth.login({
        username: userData.username,
        password: userData.password
      });

      // Set token for authenticated requests
      this.client.setApiKey(tokenResponse.access_token);

      // Generate permanent API key
      const apiKeyResponse = await this.client.auth.generateApiKey();
      
      return {
        user,
        apiKey: apiKeyResponse.api_key,
        jwtToken: tokenResponse.access_token
      };
    } catch (error) {
      console.error('Registration failed:', error);
      throw error;
    }
  }

  async getCurrentUserInfo() {
    return await this.client.auth.getCurrentUser();
  }
}

// Usage
const authManager = new AuthenticationManager('https://api.brandgpt.com');
const { user, apiKey } = await authManager.registerAndSetupUser({
  username: 'john_doe',
  email: 'john@company.com',
  password: 'secure_password_123'
});

// Store API key securely for future use
process.env.BRANDGPT_API_KEY = apiKey;
```

---

## Session Management

### Understanding Sessions

Sessions in BrandGPT are containers for organizing related content and queries. Each session maintains its own context and can contain multiple documents.

```typescript
interface SessionWorkflow {
  client: BrandGPTClient;
  
  async createProjectSession(projectName: string, description?: string) {
    const session = await this.client.sessions.create({
      name: `Project: ${projectName}`,
      // Optional: Use a prompt template for consistent behavior
      // prompt_id: 1
    });
    
    console.log(`Created session: ${session.id} for project: ${projectName}`);
    return session;
  }

  async listAllSessions() {
    const sessions = await this.client.sessions.list();
    
    // Group sessions by creation date
    const grouped = sessions.reduce((acc, session) => {
      const date = new Date(session.created_at).toDateString();
      if (!acc[date]) acc[date] = [];
      acc[date].push(session);
      return acc;
    }, {} as Record<string, typeof sessions>);
    
    return grouped;
  }

  async getSessionStats(sessionId: string) {
    const documents = await this.client.documents.listBySession(sessionId);
    
    const stats = {
      totalDocuments: documents.length,
      processingStatus: documents.reduce((acc, doc) => {
        acc[doc.processed] = (acc[doc.processed] || 0) + 1;
        return acc;
      }, {} as Record<string, number>),
      contentTypes: documents.reduce((acc, doc) => {
        acc[doc.content_type] = (acc[doc.content_type] || 0) + 1;
        return acc;
      }, {} as Record<string, number>),
      groups: [...new Set(documents.map(doc => doc.group_id).filter(Boolean))]
    };
    
    return stats;
  }
}
```

---

## Content Ingestion

### File Upload Patterns

```typescript
import fs from 'fs';
import path from 'path';

class DocumentIngestion {
  constructor(private client: BrandGPTClient) {}

  async uploadSingleFile(filePath: string, sessionId: string, groupId?: string) {
    const filename = path.basename(filePath);
    const fileBuffer = fs.readFileSync(filePath);
    
    const result = await this.client.ingestion.uploadFile(
      fileBuffer,
      filename,
      sessionId,
      { groupId }
    );

    console.log(`Uploaded ${filename}:`, result);
    return result;
  }

  async uploadMultipleFiles(
    filePaths: string[], 
    sessionId: string, 
    groupId?: string
  ) {
    const results = [];
    
    for (const filePath of filePaths) {
      try {
        const result = await this.uploadSingleFile(filePath, sessionId, groupId);
        results.push({ filePath, success: true, result });
        
        // Add delay between uploads to avoid overwhelming the API
        await new Promise(resolve => setTimeout(resolve, 1000));
      } catch (error) {
        console.error(`Failed to upload ${filePath}:`, error);
        results.push({ filePath, success: false, error: error.message });
      }
    }
    
    return results;
  }

  async uploadDirectory(
    dirPath: string, 
    sessionId: string, 
    options: { 
      groupId?: string; 
      extensions?: string[];
      recursive?: boolean;
    } = {}
  ) {
    const { groupId, extensions = ['.pdf', '.txt', '.md', '.docx'], recursive = false } = options;
    
    const getFiles = (dir: string): string[] => {
      const files: string[] = [];
      const items = fs.readdirSync(dir, { withFileTypes: true });
      
      for (const item of items) {
        const fullPath = path.join(dir, item.name);
        
        if (item.isDirectory() && recursive) {
          files.push(...getFiles(fullPath));
        } else if (item.isFile() && extensions.includes(path.extname(item.name))) {
          files.push(fullPath);
        }
      }
      
      return files;
    };

    const files = getFiles(dirPath);
    console.log(`Found ${files.length} files to upload`);
    
    return await this.uploadMultipleFiles(files, sessionId, groupId);
  }

  async uploadFromStream(
    stream: NodeJS.ReadableStream,
    filename: string,
    sessionId: string,
    groupId?: string
  ) {
    const result = await this.client.ingestion.uploadFile(
      stream,
      filename,
      sessionId,
      { groupId }
    );

    return result;
  }
}

// Usage Example
const ingestion = new DocumentIngestion(client);

// Upload single file
const session = await client.sessions.create({ name: 'Research Project' });
await ingestion.uploadSingleFile('./research-paper.pdf', session.id, 'research');

// Upload multiple files
const files = ['./doc1.pdf', './doc2.txt', './doc3.md'];
const results = await ingestion.uploadMultipleFiles(files, session.id, 'batch-1');

// Upload entire directory
await ingestion.uploadDirectory('./documents', session.id, {
  groupId: 'company-docs',
  extensions: ['.pdf', '.docx', '.txt'],
  recursive: true
});
```

### URL Scraping Strategies

```typescript
class WebContentIngestion {
  constructor(private client: BrandGPTClient) {}

  async scrapeCompanyWebsite(
    baseUrl: string, 
    sessionId: string,
    options: {
      maxDepth?: number;
      maxPages?: number;
      groupId?: string;
    } = {}
  ) {
    const { maxDepth = 2, maxPages = 50, groupId = 'website' } = options;

    try {
      const result = await this.client.ingestion.ingestUrl(baseUrl, {
        maxDepth,
        maxLinksPerPage: maxPages,
        sessionId,
        groupId
      });

      console.log(`Started scraping ${baseUrl}:`, result);
      return result;
    } catch (error) {
      console.error(`Failed to scrape ${baseUrl}:`, error);
      throw error;
    }
  }

  async scrapeMultipleUrls(
    urls: string[], 
    sessionId: string, 
    groupId?: string
  ) {
    const results = [];

    for (const url of urls) {
      try {
        const result = await this.client.ingestion.ingestUrl(url, {
          maxDepth: 1, // Single page for multiple URLs
          sessionId,
          groupId
        });
        
        results.push({ url, success: true, result });
        
        // Delay between requests to be respectful
        await new Promise(resolve => setTimeout(resolve, 2000));
      } catch (error) {
        results.push({ url, success: false, error: error.message });
      }
    }

    return results;
  }

  async scrapeNewsArticles(articleUrls: string[], sessionId: string) {
    return this.scrapeMultipleUrls(articleUrls, sessionId, 'news-articles');
  }

  async scrapeBlogPosts(blogUrls: string[], sessionId: string) {
    return this.scrapeMultipleUrls(blogUrls, sessionId, 'blog-posts');
  }
}
```

### Structured Data Ingestion

```typescript
interface ProductCatalog {
  products: Array<{
    id: string;
    name: string;
    category: string;
    price: number;
    description: string;
    features: string[];
    specifications: Record<string, any>;
  }>;
}

class StructuredDataManager {
  constructor(private client: BrandGPTClient) {}

  async ingestProductCatalog(catalog: ProductCatalog, sessionId: string) {
    const result = await this.client.ingestion.ingestStructuredData({
      data: catalog,
      sessionId,
      groupId: 'product-catalog',
      metadata: {
        type: 'product_catalog',
        version: '1.0',
        timestamp: new Date().toISOString(),
        productCount: catalog.products.length
      }
    });

    return result;
  }

  async ingestCustomerData(customers: any[], sessionId: string) {
    // Process in batches to avoid large payloads
    const batchSize = 100;
    const results = [];

    for (let i = 0; i < customers.length; i += batchSize) {
      const batch = customers.slice(i, i + batchSize);
      
      const result = await this.client.ingestion.ingestStructuredData({
        data: { customers: batch },
        sessionId,
        groupId: 'customer-data',
        metadata: {
          batch: Math.floor(i / batchSize) + 1,
          batchSize: batch.length,
          totalCustomers: customers.length
        }
      });

      results.push(result);
      
      // Small delay between batches
      await new Promise(resolve => setTimeout(resolve, 500));
    }

    return results;
  }

  async ingestApiResponse(
    apiData: any, 
    sessionId: string, 
    apiName: string
  ) {
    return await this.client.ingestion.ingestStructuredData({
      data: apiData,
      sessionId,
      groupId: `api-${apiName}`,
      metadata: {
        source: 'api',
        apiName,
        timestamp: new Date().toISOString(),
        dataType: typeof apiData
      }
    });
  }

  async ingestDatabaseExport(
    tableData: Record<string, any[]>, 
    sessionId: string
  ) {
    const results = [];

    for (const [tableName, records] of Object.entries(tableData)) {
      const result = await this.client.ingestion.ingestStructuredData({
        data: { [tableName]: records },
        sessionId,
        groupId: `database-${tableName}`,
        metadata: {
          source: 'database',
          table: tableName,
          recordCount: records.length,
          exportDate: new Date().toISOString()
        }
      });

      results.push({ table: tableName, result });
    }

    return results;
  }
}
```

---

## Querying and Retrieval

### Basic Query Patterns

```typescript
class QueryManager {
  constructor(private client: BrandGPTClient) {}

  async simpleQuery(question: string, sessionId: string) {
    const response = await this.client.query.query({
      query: question,
      sessionId,
      maxResults: 5
    });

    return {
      answer: response.response,
      sources: response.sources.map(source => ({
        text: source.text.substring(0, 200) + '...',
        document: source.metadata.filename || 'Unknown',
        confidence: source.metadata.score || 'N/A'
      }))
    };
  }

  async contextualQuery(
    question: string, 
    sessionId: string, 
    groupId?: string
  ) {
    return await this.client.query.query({
      query: question,
      sessionId,
      groupId, // Limit search to specific group
      maxResults: 10
    });
  }

  async multipleRelatedQueries(
    questions: string[], 
    sessionId: string
  ) {
    const results = [];

    for (const question of questions) {
      const response = await this.simpleQuery(question, sessionId);
      results.push({ question, ...response });
      
      // Small delay between queries
      await new Promise(resolve => setTimeout(resolve, 500));
    }

    return results;
  }

  async generateSummary(sessionId: string, topic?: string) {
    const summaryQuery = topic 
      ? `Provide a comprehensive summary of all information related to ${topic}.`
      : 'Provide a comprehensive summary of all the ingested content.';

    return await this.client.query.query({
      query: summaryQuery,
      sessionId,
      maxResults: 20 // Get more context for summary
    });
  }

  async askFollowUpQuestions(
    originalQuery: string,
    originalResponse: string,
    sessionId: string
  ) {
    const followUpQuery = `Based on the previous question "${originalQuery}" and the response "${originalResponse.substring(0, 500)}...", what additional questions should I ask to get more comprehensive information?`;

    return await this.client.query.query({
      query: followUpQuery,
      sessionId
    });
  }
}
```

### Advanced Query Strategies

```typescript
class AdvancedQueryStrategies {
  constructor(private client: BrandGPTClient) {}

  async comparativeAnalysis(
    items: string[], 
    sessionId: string, 
    aspect: string = 'features'
  ) {
    const itemList = items.join(', ');
    const query = `Compare and contrast ${itemList} in terms of their ${aspect}. Provide a detailed analysis highlighting similarities and differences.`;

    const response = await this.client.query.query({
      query,
      sessionId,
      maxResults: 15
    });

    return {
      comparison: response.response,
      sources: response.sources,
      items,
      aspect
    };
  }

  async trendAnalysis(sessionId: string, timeframe: string = 'recent') {
    const query = `Analyze trends and patterns in the data. Focus on ${timeframe} developments and emerging themes. Identify key insights and predictions.`;

    return await this.client.query.query({
      query,
      sessionId,
      maxResults: 20
    });
  }

  async riskAssessment(topic: string, sessionId: string) {
    const query = `Conduct a comprehensive risk assessment for ${topic}. Identify potential risks, their likelihood, impact, and mitigation strategies based on the available information.`;

    return await this.client.query.query({
      query,
      sessionId,
      maxResults: 15
    });
  }

  async decisionSupport(
    decision: string, 
    criteria: string[], 
    sessionId: string
  ) {
    const criteriaList = criteria.join(', ');
    const query = `Help me make a decision about ${decision}. Evaluate options based on these criteria: ${criteriaList}. Provide recommendations with supporting evidence.`;

    return await this.client.query.query({
      query,
      sessionId,
      maxResults: 20
    });
  }

  async expertConsultation(
    question: string, 
    expertiseArea: string, 
    sessionId: string
  ) {
    const query = `As an expert in ${expertiseArea}, provide a detailed professional analysis of: ${question}. Include technical insights, best practices, and industry standards.`;

    return await this.client.query.query({
      query,
      sessionId,
      maxResults: 12
    });
  }

  async scenarioPlanning(
    scenario: string, 
    variables: string[], 
    sessionId: string
  ) {
    const variablesList = variables.join(', ');
    const query = `Analyze the scenario: ${scenario}. Consider how these variables might affect outcomes: ${variablesList}. Provide multiple scenario outcomes and their implications.`;

    return await this.client.query.query({
      query,
      sessionId,
      maxResults: 18
    });
  }
}
```

---

## Advanced Usage Patterns

### Session-Based Workflows

```typescript
class WorkflowManager {
  constructor(private client: BrandGPTClient) {}

  async createResearchWorkflow(topic: string) {
    // 1. Create dedicated session
    const session = await this.client.sessions.create({
      name: `Research: ${topic}`
    });

    // 2. Define workflow steps
    const workflow = {
      sessionId: session.id,
      topic,
      steps: [
        'literature-review',
        'data-collection',
        'analysis',
        'synthesis',
        'conclusions'
      ],
      currentStep: 0,
      documents: [] as any[]
    };

    return workflow;
  }

  async executeWorkflowStep(
    workflow: any, 
    stepName: string, 
    inputs: any[]
  ) {
    const groupId = `${workflow.topic}-${stepName}`;
    const results = [];

    // Process inputs for current step
    for (const input of inputs) {
      if (input.type === 'file') {
        const result = await this.client.ingestion.uploadFile(
          input.content,
          input.filename,
          workflow.sessionId,
          { groupId }
        );
        results.push(result);
      } else if (input.type === 'url') {
        const result = await this.client.ingestion.ingestUrl(
          input.url,
          { sessionId: workflow.sessionId, groupId }
        );
        results.push(result);
      } else if (input.type === 'data') {
        const result = await this.client.ingestion.ingestStructuredData({
          data: input.data,
          sessionId: workflow.sessionId,
          groupId,
          metadata: { step: stepName }
        });
        results.push(result);
      }
    }

    // Update workflow progress
    workflow.currentStep++;
    workflow.documents.push(...results);

    return { workflow, stepResults: results };
  }

  async generateStepReport(workflow: any, stepName: string) {
    const query = `Generate a comprehensive report for the ${stepName} step of research on ${workflow.topic}. Summarize findings, key insights, and recommendations for next steps.`;

    return await this.client.query.query({
      query,
      sessionId: workflow.sessionId,
      groupId: `${workflow.topic}-${stepName}`
    });
  }
}
```

### Data Pipeline Integration

```typescript
class DataPipelineIntegration {
  constructor(private client: BrandGPTClient) {}

  async createIngestionPipeline(
    pipelineName: string,
    sources: Array<{
      type: 'file' | 'url' | 'api' | 'database';
      config: any;
      schedule?: string;
    }>
  ) {
    const session = await this.client.sessions.create({
      name: `Pipeline: ${pipelineName}`
    });

    const pipeline = {
      name: pipelineName,
      sessionId: session.id,
      sources,
      status: 'active',
      lastRun: null as Date | null,
      nextRun: null as Date | null
    };

    return pipeline;
  }

  async executePipeline(pipeline: any) {
    pipeline.lastRun = new Date();
    const results = [];

    for (const source of pipeline.sources) {
      try {
        let result;

        switch (source.type) {
          case 'file':
            result = await this.processFileSource(source, pipeline.sessionId);
            break;
          case 'url':
            result = await this.processUrlSource(source, pipeline.sessionId);
            break;
          case 'api':
            result = await this.processApiSource(source, pipeline.sessionId);
            break;
          case 'database':
            result = await this.processDatabaseSource(source, pipeline.sessionId);
            break;
        }

        results.push({ source: source.type, success: true, result });
      } catch (error) {
        results.push({ source: source.type, success: false, error: error.message });
      }
    }

    return results;
  }

  private async processFileSource(source: any, sessionId: string) {
    const { directory, pattern, groupId } = source.config;
    // Implementation for file processing
    // This would typically involve directory scanning and file upload
  }

  private async processUrlSource(source: any, sessionId: string) {
    const { urls, maxDepth, groupId } = source.config;
    const results = [];

    for (const url of urls) {
      const result = await this.client.ingestion.ingestUrl(url, {
        maxDepth,
        sessionId,
        groupId
      });
      results.push(result);
    }

    return results;
  }

  private async processApiSource(source: any, sessionId: string) {
    const { endpoint, headers, groupId } = source.config;
    
    // Fetch data from API
    const response = await fetch(endpoint, { headers });
    const data = await response.json();

    // Ingest structured data
    return await this.client.ingestion.ingestStructuredData({
      data,
      sessionId,
      groupId,
      metadata: {
        source: 'api',
        endpoint,
        timestamp: new Date().toISOString()
      }
    });
  }

  private async processDatabaseSource(source: any, sessionId: string) {
    const { connectionString, query, groupId } = source.config;
    
    // This would typically involve database connection and query execution
    // Implementation depends on specific database type
    throw new Error('Database source processing not implemented in this example');
  }
}
```

### Real-time Query Processing

```typescript
class RealTimeQueryProcessor {
  private queryQueue: Array<{
    id: string;
    query: string;
    sessionId: string;
    timestamp: Date;
    priority: number;
  }> = [];

  constructor(private client: BrandGPTClient) {}

  async addQuery(
    query: string, 
    sessionId: string, 
    priority: number = 1
  ): Promise<string> {
    const queryId = `query_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    this.queryQueue.push({
      id: queryId,
      query,
      sessionId,
      timestamp: new Date(),
      priority
    });

    // Sort by priority (higher first) then by timestamp
    this.queryQueue.sort((a, b) => {
      if (b.priority !== a.priority) return b.priority - a.priority;
      return a.timestamp.getTime() - b.timestamp.getTime();
    });

    // Process queue
    this.processQueue();

    return queryId;
  }

  private async processQueue() {
    if (this.queryQueue.length === 0) return;

    const query = this.queryQueue.shift()!;
    
    try {
      const result = await this.client.query.query({
        query: query.query,
        sessionId: query.sessionId
      });

      // Emit result (in real app, this might be through WebSocket or event emitter)
      this.handleQueryResult(query.id, result);
      
    } catch (error) {
      this.handleQueryError(query.id, error);
    }

    // Continue processing queue
    setTimeout(() => this.processQueue(), 100);
  }

  private handleQueryResult(queryId: string, result: any) {
    console.log(`Query ${queryId} completed:`, result);
    // In real implementation, emit to WebSocket or event system
  }

  private handleQueryError(queryId: string, error: any) {
    console.error(`Query ${queryId} failed:`, error);
    // In real implementation, emit error to WebSocket or event system
  }

  getQueueStatus() {
    return {
      pending: this.queryQueue.length,
      queue: this.queryQueue.map(q => ({
        id: q.id,
        priority: q.priority,
        timestamp: q.timestamp
      }))
    };
  }
}
```

---

## Error Handling

### Comprehensive Error Management

```typescript
import { BrandGPTError } from '@marcapo/brandgpt-client';

class ErrorHandler {
  static handleApiError(error: any): never {
    if (error instanceof BrandGPTError) {
      switch (error.statusCode) {
        case 401:
          throw new Error('Authentication failed. Please check your API key.');
        case 403:
          throw new Error('Access forbidden. You may not have permission for this operation.');
        case 404:
          throw new Error('Resource not found. The requested item may not exist.');
        case 429:
          throw new Error('Rate limit exceeded. Please wait before making more requests.');
        case 500:
          throw new Error('Server error. Please try again later.');
        default:
          throw new Error(`API Error (${error.statusCode}): ${error.message}`);
      }
    }
    
    throw new Error(`Unexpected error: ${error.message}`);
  }

  static async withRetry<T>(
    operation: () => Promise<T>,
    maxRetries: number = 3,
    delayMs: number = 1000
  ): Promise<T> {
    let lastError: any;

    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        return await operation();
      } catch (error) {
        lastError = error;
        
        // Don't retry for client errors (4xx)
        if (error instanceof BrandGPTError && error.statusCode && error.statusCode < 500) {
          throw error;
        }

        if (attempt === maxRetries) {
          break;
        }

        console.warn(`Attempt ${attempt} failed, retrying in ${delayMs}ms...`);
        await new Promise(resolve => setTimeout(resolve, delayMs * attempt));
      }
    }

    throw lastError;
  }
}

// Resilient Query Manager
class ResilientQueryManager {
  constructor(private client: BrandGPTClient) {}

  async safeQuery(query: string, sessionId: string, options: {
    maxRetries?: number;
    timeout?: number;
    fallbackResponse?: string;
  } = {}) {
    const { maxRetries = 3, timeout = 30000, fallbackResponse } = options;

    try {
      return await ErrorHandler.withRetry(async () => {
        // Set timeout for the query
        const timeoutPromise = new Promise((_, reject) => 
          setTimeout(() => reject(new Error('Query timeout')), timeout)
        );

        const queryPromise = this.client.query.query({
          query,
          sessionId
        });

        return await Promise.race([queryPromise, timeoutPromise]);
      }, maxRetries);

    } catch (error) {
      console.error('Query failed after retries:', error);
      
      if (fallbackResponse) {
        return {
          response: fallbackResponse,
          sources: [],
          error: error.message
        };
      }
      
      ErrorHandler.handleApiError(error);
    }
  }

  async batchSafeQuery(
    queries: Array<{ query: string; sessionId: string }>,
    options: {
      concurrency?: number;
      continueOnError?: boolean;
    } = {}
  ) {
    const { concurrency = 3, continueOnError = true } = options;
    const results = [];
    
    // Process queries in batches
    for (let i = 0; i < queries.length; i += concurrency) {
      const batch = queries.slice(i, i + concurrency);
      
      const batchPromises = batch.map(async ({ query, sessionId }) => {
        try {
          const result = await this.safeQuery(query, sessionId);
          return { query, sessionId, success: true, result };
        } catch (error) {
          if (!continueOnError) throw error;
          return { query, sessionId, success: false, error: error.message };
        }
      });

      const batchResults = await Promise.all(batchPromises);
      results.push(...batchResults);
    }

    return results;
  }
}
```

---

## Performance Optimization

### Caching and Rate Limiting

```typescript
class PerformanceOptimizer {
  private queryCache = new Map<string, { result: any; timestamp: number }>();
  private rateLimiter = new Map<string, number[]>();
  private readonly CACHE_TTL = 5 * 60 * 1000; // 5 minutes
  private readonly RATE_LIMIT = 10; // 10 requests per minute

  constructor(private client: BrandGPTClient) {}

  private getCacheKey(query: string, sessionId: string): string {
    return `${sessionId}:${Buffer.from(query).toString('base64')}`;
  }

  private isRateLimited(sessionId: string): boolean {
    const now = Date.now();
    const requests = this.rateLimiter.get(sessionId) || [];
    
    // Remove requests older than 1 minute
    const recentRequests = requests.filter(time => now - time < 60000);
    this.rateLimiter.set(sessionId, recentRequests);
    
    return recentRequests.length >= this.RATE_LIMIT;
  }

  private addToRateLimit(sessionId: string) {
    const requests = this.rateLimiter.get(sessionId) || [];
    requests.push(Date.now());
    this.rateLimiter.set(sessionId, requests);
  }

  async optimizedQuery(query: string, sessionId: string) {
    const cacheKey = this.getCacheKey(query, sessionId);
    
    // Check cache first
    const cached = this.queryCache.get(cacheKey);
    if (cached && Date.now() - cached.timestamp < this.CACHE_TTL) {
      console.log('Returning cached result for query');
      return cached.result;
    }

    // Check rate limit
    if (this.isRateLimited(sessionId)) {
      throw new Error('Rate limit exceeded for this session');
    }

    // Make API call
    const result = await this.client.query.query({ query, sessionId });
    
    // Cache result
    this.queryCache.set(cacheKey, {
      result,
      timestamp: Date.now()
    });

    // Add to rate limiter
    this.addToRateLimit(sessionId);

    return result;
  }

  clearCache(sessionId?: string) {
    if (sessionId) {
      // Clear cache for specific session
      const keysToDelete = Array.from(this.queryCache.keys())
        .filter(key => key.startsWith(sessionId));
      keysToDelete.forEach(key => this.queryCache.delete(key));
    } else {
      // Clear all cache
      this.queryCache.clear();
    }
  }

  getCacheStats() {
    const now = Date.now();
    const validEntries = Array.from(this.queryCache.values())
      .filter(entry => now - entry.timestamp < this.CACHE_TTL);
    
    return {
      totalEntries: this.queryCache.size,
      validEntries: validEntries.length,
      hitRate: validEntries.length / this.queryCache.size || 0
    };
  }
}
```

### Batch Processing

```typescript
class BatchProcessor {
  constructor(private client: BrandGPTClient) {}

  async batchIngestFiles(
    files: Array<{ path: string; filename: string }>,
    sessionId: string,
    options: {
      batchSize?: number;
      delayMs?: number;
      groupId?: string;
      onProgress?: (completed: number, total: number) => void;
    } = {}
  ) {
    const { batchSize = 5, delayMs = 1000, groupId, onProgress } = options;
    const results = [];
    const total = files.length;

    for (let i = 0; i < files.length; i += batchSize) {
      const batch = files.slice(i, i + batchSize);
      
      const batchPromises = batch.map(async ({ path, filename }) => {
        try {
          const fs = require('fs');
          const fileBuffer = fs.readFileSync(path);
          
          const result = await this.client.ingestion.uploadFile(
            fileBuffer,
            filename,
            sessionId,
            { groupId }
          );
          
          return { path, filename, success: true, result };
        } catch (error) {
          return { path, filename, success: false, error: error.message };
        }
      });

      const batchResults = await Promise.all(batchPromises);
      results.push(...batchResults);

      // Report progress
      if (onProgress) {
        onProgress(Math.min(i + batchSize, total), total);
      }

      // Delay between batches
      if (i + batchSize < files.length) {
        await new Promise(resolve => setTimeout(resolve, delayMs));
      }
    }

    return results;
  }

  async batchQueries(
    queries: Array<{ query: string; sessionId: string; id?: string }>,
    options: {
      batchSize?: number;
      delayMs?: number;
      onProgress?: (completed: number, total: number) => void;
    } = {}
  ) {
    const { batchSize = 3, delayMs = 500, onProgress } = options;
    const results = [];
    const total = queries.length;

    for (let i = 0; i < queries.length; i += batchSize) {
      const batch = queries.slice(i, i + batchSize);
      
      const batchPromises = batch.map(async ({ query, sessionId, id }) => {
        try {
          const result = await this.client.query.query({ query, sessionId });
          return { id, query, sessionId, success: true, result };
        } catch (error) {
          return { id, query, sessionId, success: false, error: error.message };
        }
      });

      const batchResults = await Promise.all(batchPromises);
      results.push(...batchResults);

      // Report progress
      if (onProgress) {
        onProgress(Math.min(i + batchSize, total), total);
      }

      // Delay between batches
      if (i + batchSize < queries.length) {
        await new Promise(resolve => setTimeout(resolve, delayMs));
      }
    }

    return results;
  }
}
```

---

## Best Practices

### 1. Session Organization

```typescript
// ✅ Good: Organized session structure
class SessionOrganizer {
  async createProjectStructure(projectName: string) {
    const mainSession = await client.sessions.create({
      name: `${projectName} - Main`
    });

    const subSessions = {
      research: await client.sessions.create({ name: `${projectName} - Research` }),
      analysis: await client.sessions.create({ name: `${projectName} - Analysis` }),
      reports: await client.sessions.create({ name: `${projectName} - Reports` })
    };

    return { mainSession, subSessions };
  }
}

// ❌ Bad: All content in one session without organization
// Don't put unrelated content in the same session
```

### 2. Group Management

```typescript
// ✅ Good: Logical grouping
const groups = {
  contracts: 'legal-contracts',
  policies: 'company-policies', 
  research: 'market-research',
  financial: 'financial-reports'
};

await client.ingestion.uploadFile(
  contractBuffer,
  'contract-2024.pdf',
  sessionId,
  { groupId: groups.contracts }
);

// ❌ Bad: No grouping or inconsistent naming
// { groupId: 'misc-stuff' }
```

### 3. Error Handling

```typescript
// ✅ Good: Comprehensive error handling
async function safeUpload(file: Buffer, filename: string, sessionId: string) {
  try {
    return await client.ingestion.uploadFile(file, filename, sessionId);
  } catch (error) {
    if (error instanceof BrandGPTError) {
      if (error.statusCode === 413) {
        throw new Error('File too large. Please use a smaller file.');
      }
      if (error.statusCode === 415) {
        throw new Error('Unsupported file type. Please use PDF or text files.');
      }
    }
    throw error;
  }
}

// ❌ Bad: No error handling
// Just await client.ingestion.uploadFile(...) without try-catch
```

### 4. Resource Cleanup

```typescript
// ✅ Good: Proper cleanup
class ResourceManager {
  private sessions: string[] = [];

  async cleanup() {
    for (const sessionId of this.sessions) {
      try {
        await client.documents.delete({ sessionId });
      } catch (error) {
        console.warn(`Failed to cleanup session ${sessionId}:`, error);
      }
    }
    this.sessions = [];
  }

  async createManagedSession(name: string) {
    const session = await client.sessions.create({ name });
    this.sessions.push(session.id);
    return session;
  }
}

// ❌ Bad: Creating sessions without cleanup strategy
```

---

## Real-World Examples

### Example 1: Document Analysis System

```typescript
class DocumentAnalysisSystem {
  constructor(private client: BrandGPTClient) {}

  async analyzeCompanyDocuments(documentPaths: string[]) {
    // Create dedicated session
    const session = await this.client.sessions.create({
      name: `Document Analysis - ${new Date().toISOString()}`
    });

    // Upload documents with progress tracking
    console.log('Uploading documents...');
    const uploadResults = [];
    for (let i = 0; i < documentPaths.length; i++) {
      const path = documentPaths[i];
      const filename = require('path').basename(path);
      const fileBuffer = require('fs').readFileSync(path);

      try {
        const result = await this.client.ingestion.uploadFile(
          fileBuffer,
          filename,
          session.id,
          { groupId: 'company-docs' }
        );
        
        uploadResults.push({ filename, success: true, result });
        console.log(`✅ Uploaded ${filename} (${i + 1}/${documentPaths.length})`);
      } catch (error) {
        uploadResults.push({ filename, success: false, error: error.message });
        console.error(`❌ Failed to upload ${filename}:`, error);
      }

      // Small delay to avoid overwhelming the API
      await new Promise(resolve => setTimeout(resolve, 1000));
    }

    // Wait for processing
    console.log('Waiting for document processing...');
    await new Promise(resolve => setTimeout(resolve, 5000));

    // Perform analysis queries
    const analysisQueries = [
      'What are the main topics covered in these documents?',
      'What are the key risks mentioned across all documents?',
      'What are the most important dates and deadlines?',
      'Who are the key stakeholders mentioned?',
      'What action items or recommendations are provided?'
    ];

    const analysisResults = [];
    for (const query of analysisQueries) {
      try {
        const response = await this.client.query.query({
          query,
          sessionId: session.id,
          maxResults: 10
        });
        
        analysisResults.push({
          question: query,
          answer: response.response,
          sourceCount: response.sources.length,
          sources: response.sources.map(s => s.metadata.filename).filter(Boolean)
        });

        console.log(`✅ Analyzed: ${query}`);
      } catch (error) {
        analysisResults.push({
          question: query,
          error: error.message
        });
        console.error(`❌ Failed query: ${query}`);
      }
    }

    // Generate summary report
    const summaryResponse = await this.client.query.query({
      query: 'Generate a comprehensive executive summary of all the analyzed documents, highlighting key insights, risks, opportunities, and recommendations.',
      sessionId: session.id,
      maxResults: 20
    });

    return {
      sessionId: session.id,
      uploadResults,
      analysisResults,
      executiveSummary: summaryResponse.response,
      totalDocuments: documentPaths.length,
      successfulUploads: uploadResults.filter(r => r.success).length
    };
  }
}

// Usage
const analyzer = new DocumentAnalysisSystem(client);
const results = await analyzer.analyzeCompanyDocuments([
  './contracts/contract-a.pdf',
  './contracts/contract-b.pdf',
  './policies/hr-policy.pdf',
  './reports/quarterly-report.pdf'
]);

console.log('Analysis Results:', results);
```

### Example 2: Customer Support Knowledge Base

```typescript
class CustomerSupportKB {
  constructor(private client: BrandGPTClient) {}

  async buildKnowledgeBase(sources: {
    manuals: string[];
    faqs: string[];
    webUrls: string[];
    apiDocs: any[];
  }) {
    const session = await this.client.sessions.create({
      name: 'Customer Support Knowledge Base'
    });

    const ingestionResults = {
      manuals: [],
      faqs: [],
      webContent: [],
      apiDocs: []
    };

    // Ingest product manuals
    for (const manualPath of sources.manuals) {
      try {
        const fileBuffer = require('fs').readFileSync(manualPath);
        const filename = require('path').basename(manualPath);
        
        const result = await this.client.ingestion.uploadFile(
          fileBuffer,
          filename,
          session.id,
          { groupId: 'product-manuals' }
        );
        
        ingestionResults.manuals.push({ filename, success: true, result });
      } catch (error) {
        ingestionResults.manuals.push({ filename: manualPath, success: false, error });
      }
    }

    // Ingest FAQ documents
    for (const faqPath of sources.faqs) {
      try {
        const fileBuffer = require('fs').readFileSync(faqPath);
        const filename = require('path').basename(faqPath);
        
        const result = await this.client.ingestion.uploadFile(
          fileBuffer,
          filename,
          session.id,
          { groupId: 'faqs' }
        );
        
        ingestionResults.faqs.push({ filename, success: true, result });
      } catch (error) {
        ingestionResults.faqs.push({ filename: faqPath, success: false, error });
      }
    }

    // Ingest web content
    for (const url of sources.webUrls) {
      try {
        const result = await this.client.ingestion.ingestUrl(url, {
          maxDepth: 1,
          sessionId: session.id,
          groupId: 'web-content'
        });
        
        ingestionResults.webContent.push({ url, success: true, result });
      } catch (error) {
        ingestionResults.webContent.push({ url, success: false, error });
      }
    }

    // Ingest API documentation
    for (const apiDoc of sources.apiDocs) {
      try {
        const result = await this.client.ingestion.ingestStructuredData({
          data: apiDoc,
          sessionId: session.id,
          groupId: 'api-docs',
          metadata: {
            type: 'api_documentation',
            version: apiDoc.version || '1.0'
          }
        });
        
        ingestionResults.apiDocs.push({ success: true, result });
      } catch (error) {
        ingestionResults.apiDocs.push({ success: false, error });
      }
    }

    return {
      sessionId: session.id,
      ingestionResults
    };
  }

  async handleCustomerQuery(
    query: string, 
    sessionId: string,
    customerContext: {
      productVersion?: string;
      userType?: 'basic' | 'premium' | 'enterprise';
      previousIssues?: string[];
    } = {}
  ) {
    // Enhance query with context
    let enhancedQuery = query;
    
    if (customerContext.productVersion) {
      enhancedQuery += ` (Product version: ${customerContext.productVersion})`;
    }
    
    if (customerContext.userType) {
      enhancedQuery += ` (User type: ${customerContext.userType})`;
    }

    // First, try to find direct answers
    const directResponse = await this.client.query.query({
      query: enhancedQuery,
      sessionId,
      maxResults: 5
    });

    // If no good direct answer, try troubleshooting approach
    let troubleshootingResponse = null;
    if (directResponse.sources.length === 0 || 
        directResponse.response.includes("I don't have") || 
        directResponse.response.includes("I couldn't find")) {
      
      troubleshootingResponse = await this.client.query.query({
        query: `Provide troubleshooting steps and potential solutions for: ${query}`,
        sessionId,
        maxResults: 8
      });
    }

    // Generate escalation recommendations
    const escalationResponse = await this.client.query.query({
      query: `When should this issue "${query}" be escalated to human support, and what information should be gathered?`,
      sessionId,
      maxResults: 3
    });

    return {
      directAnswer: directResponse,
      troubleshooting: troubleshootingResponse,
      escalation: escalationResponse,
      confidence: directResponse.sources.length > 0 ? 'high' : 'low',
      recommendedAction: directResponse.sources.length > 0 ? 'provide_answer' : 'escalate_to_human'
    };
  }

  async generateKBMetrics(sessionId: string) {
    const documents = await this.client.documents.listBySession(sessionId);
    
    const metrics = {
      totalDocuments: documents.length,
      documentsByGroup: documents.reduce((acc, doc) => {
        const group = doc.group_id || 'ungrouped';
        acc[group] = (acc[group] || 0) + 1;
        return acc;
      }, {} as Record<string, number>),
      documentsByType: documents.reduce((acc, doc) => {
        acc[doc.content_type] = (acc[doc.content_type] || 0) + 1;
        return acc;
      }, {} as Record<string, number>),
      processingStatus: documents.reduce((acc, doc) => {
        acc[doc.processed] = (acc[doc.processed] || 0) + 1;
        return acc;
      }, {} as Record<string, number>)
    };

    return metrics;
  }
}

// Usage
const supportKB = new CustomerSupportKB(client);

// Build knowledge base
const kbResult = await supportKB.buildKnowledgeBase({
  manuals: ['./manuals/user-guide.pdf', './manuals/admin-guide.pdf'],
  faqs: ['./faqs/common-issues.txt'],
  webUrls: ['https://company.com/help', 'https://company.com/troubleshooting'],
  apiDocs: [{ endpoints: [...], version: '2.0' }]
});

// Handle customer queries
const customerResponse = await supportKB.handleCustomerQuery(
  "How do I reset my password?",
  kbResult.sessionId,
  { userType: 'premium', productVersion: '2.1' }
);

console.log('Customer Support Response:', customerResponse);
```

### Example 3: Market Research Aggregator

```typescript
class MarketResearchAggregator {
  constructor(private client: BrandGPTClient) {}

  async conductMarketResearch(topic: string, sources: {
    reports: string[];
    websites: string[];
    competitorData: any[];
    industryData: any[];
  }) {
    const session = await this.client.sessions.create({
      name: `Market Research: ${topic}`
    });

    console.log(`🔍 Starting market research for: ${topic}`);
    
    // Ingest research reports
    console.log('📊 Ingesting research reports...');
    for (const reportPath of sources.reports) {
      try {
        const fileBuffer = require('fs').readFileSync(reportPath);
        const filename = require('path').basename(reportPath);
        
        await this.client.ingestion.uploadFile(
          fileBuffer,
          filename,
          session.id,
          { groupId: 'research-reports' }
        );
        
        console.log(`✅ Ingested report: ${filename}`);
      } catch (error) {
        console.error(`❌ Failed to ingest ${reportPath}:`, error);
      }
    }

    // Scrape competitor websites
    console.log('🌐 Scraping competitor websites...');
    for (const url of sources.websites) {
      try {
        await this.client.ingestion.ingestUrl(url, {
          maxDepth: 2,
          maxLinksPerPage: 20,
          sessionId: session.id,
          groupId: 'competitor-websites'
        });
        
        console.log(`✅ Scraped: ${url}`);
      } catch (error) {
        console.error(`❌ Failed to scrape ${url}:`, error);
      }
    }

    // Ingest structured competitor data
    console.log('🏢 Ingesting competitor data...');
    for (const competitorData of sources.competitorData) {
      try {
        await this.client.ingestion.ingestStructuredData({
          data: competitorData,
          sessionId: session.id,
          groupId: 'competitor-data',
          metadata: {
            type: 'competitor_analysis',
            company: competitorData.company_name
          }
        });
        
        console.log(`✅ Ingested data for: ${competitorData.company_name}`);
      } catch (error) {
        console.error(`❌ Failed to ingest competitor data:`, error);
      }
    }

    // Ingest industry data
    console.log('🏭 Ingesting industry data...');
    for (const industryData of sources.industryData) {
      try {
        await this.client.ingestion.ingestStructuredData({
          data: industryData,
          sessionId: session.id,
          groupId: 'industry-data',
          metadata: {
            type: 'industry_analysis',
            sector: industryData.sector
          }
        });
        
        console.log(`✅ Ingested industry data for: ${industryData.sector}`);
      } catch (error) {
        console.error(`❌ Failed to ingest industry data:`, error);
      }
    }

    // Wait for processing
    console.log('⏳ Waiting for processing to complete...');
    await new Promise(resolve => setTimeout(resolve, 10000));

    // Conduct comprehensive analysis
    console.log('📈 Conducting market analysis...');
    
    const analysisQueries = [
      `What is the current market size and growth projections for ${topic}?`,
      `Who are the key competitors in the ${topic} market and what are their strengths?`,
      `What are the main market trends and drivers in ${topic}?`,
      `What are the key challenges and barriers to entry in the ${topic} market?`,
      `What opportunities exist in the ${topic} market?`,
      `What is the competitive landscape and market positioning?`,
      `What are the customer needs and pain points in ${topic}?`,
      `What are the pricing strategies used by competitors?`,
      `What are the regulatory and compliance considerations for ${topic}?`,
      `What are the technology trends impacting the ${topic} market?`
    ];

    const analysisResults = [];
    
    for (const query of analysisQueries) {
      try {
        const response = await this.client.query.query({
          query,
          sessionId: session.id,
          maxResults: 15
        });

        analysisResults.push({
          question: query,
          answer: response.response,
          sources: response.sources.map(s => ({
            source: s.metadata.filename || s.metadata.url || 'Unknown',
            relevantText: s.text.substring(0, 200) + '...'
          }))
        });

        console.log(`✅ Analyzed: ${query.substring(0, 50)}...`);
        
        // Small delay between queries
        await new Promise(resolve => setTimeout(resolve, 1000));
      } catch (error) {
        console.error(`❌ Failed query: ${query.substring(0, 50)}...`);
        analysisResults.push({
          question: query,
          error: error.message
        });
      }
    }

    // Generate executive summary
    console.log('📋 Generating executive summary...');
    const executiveSummary = await this.client.query.query({
      query: `Generate a comprehensive executive summary of the ${topic} market research. Include key findings, market opportunities, competitive landscape, and strategic recommendations. Structure it as a professional market research report.`,
      sessionId: session.id,
      maxResults: 25
    });

    // Generate SWOT analysis
    console.log('🎯 Generating SWOT analysis...');
    const swotAnalysis = await this.client.query.query({
      query: `Based on all the research data, provide a detailed SWOT analysis for entering or competing in the ${topic} market. Include Strengths, Weaknesses, Opportunities, and Threats with specific examples.`,
      sessionId: session.id,
      maxResults: 20
    });

    return {
      topic,
      sessionId: session.id,
      analysisResults,
      executiveSummary: executiveSummary.response,
      swotAnalysis: swotAnalysis.response,
      totalSources: {
        reports: sources.reports.length,
        websites: sources.websites.length,
        competitorProfiles: sources.competitorData.length,
        industryDatasets: sources.industryData.length
      },
      generatedAt: new Date().toISOString()
    };
  }

  async generateMarketReport(researchResults: any) {
    const report = `
# Market Research Report: ${researchResults.topic}
*Generated on ${new Date(researchResults.generatedAt).toLocaleDateString()}*

## Executive Summary
${researchResults.executiveSummary}

## SWOT Analysis
${researchResults.swotAnalysis}

## Detailed Analysis

${researchResults.analysisResults.map((result: any, index: number) => `
### ${index + 1}. ${result.question}
${result.answer}

**Sources:**
${result.sources?.map((source: any) => `- ${source.source}: ${source.relevantText}`).join('\n') || 'No sources available'}
`).join('\n')}

## Data Sources
- Research Reports: ${researchResults.totalSources.reports}
- Websites Analyzed: ${researchResults.totalSources.websites}
- Competitor Profiles: ${researchResults.totalSources.competitorProfiles}
- Industry Datasets: ${researchResults.totalSources.industryDatasets}

---
*This report was generated using BrandGPT RAG technology*
    `;

    return report;
  }
}

// Usage
const marketResearcher = new MarketResearchAggregator(client);

const researchResults = await marketResearcher.conductMarketResearch('Electric Vehicles', {
  reports: ['./reports/ev-market-2024.pdf', './reports/automotive-trends.pdf'],
  websites: [
    'https://electrek.co',
    'https://insideevs.com',
    'https://tesla.com/about',
    'https://www.rivian.com/about'
  ],
  competitorData: [
    { company_name: 'Tesla', market_cap: 800000000000, vehicles_sold: 1808000 },
    { company_name: 'Rivian', market_cap: 15000000000, vehicles_sold: 20000 },
    { company_name: 'Ford Lightning', market_cap: 50000000000, vehicles_sold: 15000 }
  ],
  industryData: [
    { sector: 'Electric Vehicles', growth_rate: 0.25, market_size: 500000000000 },
    { sector: 'Battery Technology', growth_rate: 0.30, market_size: 100000000000 }
  ]
});

// Generate final report
const marketReport = await marketResearcher.generateMarketReport(researchResults);
require('fs').writeFileSync('./ev-market-research-report.md', marketReport);

console.log('✅ Market research completed! Report saved to ev-market-research-report.md');
```

---

This comprehensive developer guide provides detailed examples, best practices, and real-world usage patterns for the BrandGPT Node.js client library. It should serve as a complete reference for developers building RAG applications with the BrandGPT API.