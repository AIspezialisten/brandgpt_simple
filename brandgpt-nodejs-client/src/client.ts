import { HttpClient } from './http-client';
import { AuthAPI } from './api/auth';
import { SessionsAPI } from './api/sessions';
import { IngestionAPI } from './api/ingestion';
import { QueryAPI } from './api/query';
import { DocumentsAPI } from './api/documents';
import { PromptsAPI } from './api/prompts';
import { BrandGPTConfig } from './types';

/**
 * BrandGPT API Client
 * 
 * Complete Node.js client for the BrandGPT RAG API
 * 
 * @example
 * ```typescript
 * const client = new BrandGPTClient({
 *   baseUrl: 'https://api.brandgpt.com',
 *   apiKey: 'your-api-key'
 * });
 * 
 * // Create a session
 * const session = await client.sessions.create({ name: 'My Session' });
 * 
 * // Upload a document
 * const document = await client.ingestion.uploadFile(
 *   fileBuffer,
 *   'document.pdf',
 *   session.id
 * );
 * 
 * // Query the content
 * const response = await client.query.query({
 *   query: 'What is this document about?',
 *   sessionId: session.id
 * });
 * ```
 */
export class BrandGPTClient {
  private httpClient: HttpClient;

  // API modules
  public readonly auth: AuthAPI;
  public readonly sessions: SessionsAPI;
  public readonly ingestion: IngestionAPI;
  public readonly query: QueryAPI;
  public readonly documents: DocumentsAPI;
  public readonly prompts: PromptsAPI;

  constructor(config: BrandGPTConfig) {
    this.httpClient = new HttpClient(config);

    // Initialize API modules
    this.auth = new AuthAPI(this.httpClient);
    this.sessions = new SessionsAPI(this.httpClient);
    this.ingestion = new IngestionAPI(this.httpClient);
    this.query = new QueryAPI(this.httpClient);
    this.documents = new DocumentsAPI(this.httpClient);
    this.prompts = new PromptsAPI(this.httpClient);
  }

  /**
   * Set or update the API key for authentication
   */
  setApiKey(apiKey: string): void {
    this.httpClient.setApiKey(apiKey);
  }

  /**
   * Health check endpoint
   */
  async health(): Promise<{ status: string }> {
    return this.httpClient.get('/health');
  }
}