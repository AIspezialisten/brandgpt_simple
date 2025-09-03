import { HttpClient } from '../http-client';
import { Document, DeleteRequest, DeleteResponse } from '../types';

export class DocumentsAPI {
  constructor(private client: HttpClient) {}

  /**
   * List documents in a session
   */
  async listBySession(sessionId: string): Promise<Document[]> {
    return this.client.get<Document[]>(`/api/documents/${sessionId}`);
  }

  /**
   * Delete data by various criteria
   */
  async delete(request: DeleteRequest): Promise<DeleteResponse> {
    const requestData = {
      group_id: request.groupId,
      document_id: request.documentId,
      session_id: request.sessionId,
    };

    return this.client.delete<DeleteResponse>('/api/data', {
      data: requestData,
    });
  }
}