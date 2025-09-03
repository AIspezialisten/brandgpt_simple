import { HttpClient } from '../http-client';
import { Session, SessionCreate } from '../types';

export class SessionsAPI {
  constructor(private client: HttpClient) {}

  /**
   * Create a new session
   */
  async create(sessionData: SessionCreate = {}): Promise<Session> {
    return this.client.post<Session>('/api/sessions', sessionData);
  }

  /**
   * List all sessions for the current user
   */
  async list(): Promise<Session[]> {
    return this.client.get<Session[]>('/api/sessions');
  }

  /**
   * Get a specific session by ID
   */
  async get(sessionId: string): Promise<Session> {
    return this.client.get<Session>(`/api/sessions/${sessionId}`);
  }

  /**
   * Update a session
   */
  async update(sessionId: string, updates: Partial<SessionCreate>): Promise<Session> {
    return this.client.put<Session>(`/api/sessions/${sessionId}`, updates);
  }

  /**
   * Delete a session
   */
  async delete(sessionId: string): Promise<void> {
    return this.client.delete<void>(`/api/sessions/${sessionId}`);
  }
}