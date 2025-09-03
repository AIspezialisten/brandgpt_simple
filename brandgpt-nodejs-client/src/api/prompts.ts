import { HttpClient } from '../http-client';
import { Prompt, PromptCreate } from '../types';

export class PromptsAPI {
  constructor(private client: HttpClient) {}

  /**
   * Create a new prompt template
   */
  async create(promptData: PromptCreate): Promise<Prompt> {
    return this.client.post<Prompt>('/api/prompts', promptData);
  }

  /**
   * List all prompt templates for the current user
   */
  async list(): Promise<Prompt[]> {
    return this.client.get<Prompt[]>('/api/prompts');
  }
}