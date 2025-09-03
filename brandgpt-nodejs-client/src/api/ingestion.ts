import { HttpClient } from '../http-client';
import { 
  FileIngestionOptions,
  UrlIngestionOptions,
  StructuredDataIngestion,
  IngestionStatus,
  StructuredDataResponse
} from '../types';

export class IngestionAPI {
  constructor(private client: HttpClient) {}

  /**
   * Upload and ingest a file (PDF or text)
   */
  async uploadFile(
    file: Buffer | NodeJS.ReadableStream,
    filename: string,
    sessionId: string,
    options: FileIngestionOptions = {}
  ): Promise<IngestionStatus> {
    const additionalFields: Record<string, string> = {};
    
    if (options.groupId) {
      additionalFields.group_id = options.groupId;
    }

    return this.client.uploadFile<IngestionStatus>(
      `/api/ingest/file/${sessionId}`,
      file,
      filename,
      additionalFields
    );
  }

  /**
   * Ingest content from a URL
   */
  async ingestUrl(
    url: string,
    options: UrlIngestionOptions = {}
  ): Promise<IngestionStatus> {
    const requestData = {
      url,
      max_depth: options.maxDepth,
      max_links_per_page: options.maxLinksPerPage,
      group_id: options.groupId,
      session_id: options.sessionId,
    };

    return this.client.post<IngestionStatus>('/api/ingest/url', requestData);
  }

  /**
   * Ingest structured data (JSON objects/arrays)
   */
  async ingestStructuredData(
    data: StructuredDataIngestion
  ): Promise<StructuredDataResponse> {
    const requestData = {
      data: data.data,
      session_id: data.sessionId,
      group_id: data.groupId,
      metadata: data.metadata,
    };

    return this.client.post<StructuredDataResponse>(
      '/api/ingest/structured',
      requestData
    );
  }
}