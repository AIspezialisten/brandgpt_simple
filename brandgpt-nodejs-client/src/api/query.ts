import { HttpClient } from '../http-client';
import { QueryRequest, QueryResponse } from '../types';

export class QueryAPI {
  constructor(private client: HttpClient) {}

  /**
   * Perform a RAG query against ingested content
   */
  async query(request: QueryRequest): Promise<QueryResponse> {
    const requestData = {
      query: request.query,
      session_id: request.sessionId,
      group_id: request.groupId,
      max_results: request.maxResults,
    };

    return this.client.post<QueryResponse>('/api/query', requestData);
  }
}