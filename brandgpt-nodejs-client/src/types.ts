// Core API Types
export interface BrandGPTConfig {
  baseUrl: string;
  apiKey?: string;
  timeout?: number;
}

// Authentication Types
export interface UserRegistration {
  username: string;
  email: string;
  password: string;
}

export interface UserLogin {
  username: string;
  password: string;
}

export interface User {
  id: number;
  username: string;
  email: string;
  is_active: boolean;
  created_at: string;
}

export interface Token {
  access_token: string;
  token_type: string;
}

export interface ApiKeyResponse {
  api_key: string;
  message: string;
}

// Session Types
export interface SessionCreate {
  name?: string;
  prompt_id?: number;
}

export interface Session {
  id: string;
  user_id: number;
  name?: string;
  prompt_id?: number;
  system_prompt?: string;
  created_at: string;
  updated_at?: string;
}

// Document Types
export interface Document {
  id: number;
  session_id: string;
  filename?: string;
  url?: string;
  content_type: string;
  doc_metadata?: any;
  processed: 'pending' | 'processing' | 'completed' | 'failed';
  error_message?: string;
  created_at: string;
  processed_at?: string;
  user_id: number;
  group_id?: string;
}

// Ingestion Types
export interface FileIngestionOptions {
  groupId?: string;
  sessionId?: string;
}

export interface UrlIngestionOptions {
  maxDepth?: number;
  maxLinksPerPage?: number;
  groupId?: string;
  sessionId?: string;
}

export interface StructuredDataIngestion {
  data: any;
  sessionId?: string;
  groupId?: string;
  metadata?: Record<string, any>;
}

export interface IngestionStatus {
  document_id: number;
  status: string;
  message?: string;
}

export interface StructuredDataResponse {
  document_id: number;
  status: string;
  items_processed: number;
  message: string;
}

// Query Types
export interface QueryRequest {
  query: string;
  sessionId?: string;
  groupId?: string;
  maxResults?: number;
}

export interface QuerySource {
  text: string;
  score?: number;
  content_type?: string;
  filename?: string;
  group_id?: string;
  metadata?: {
    session_id?: string;
    user_id?: number;
    document_id?: number;
    filename?: string;
    [key: string]: any;
  };
}

export interface QueryResponse {
  response: string;
  sources: QuerySource[];
  error?: string;
}

// Prompt Types
export interface PromptCreate {
  name: string;
  description?: string;
  content: string;
}

export interface Prompt {
  id: number;
  name: string;
  description?: string;
  content: string;
  user_id: number;
  created_at: string;
  updated_at?: string;
}

// Data Management Types
export interface DeleteRequest {
  groupId?: string;
  documentId?: number;
  sessionId?: string;
}

export interface DeleteResponse {
  message: string;
  deleted_count: number;
}

// Error Types
export interface ApiError {
  detail: string;
  status_code: number;
}

export class BrandGPTError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public details?: any
  ) {
    super(message);
    this.name = 'BrandGPTError';
  }
}