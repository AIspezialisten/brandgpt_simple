// Main exports
export { BrandGPTClient } from './client';
export { BrandGPTError } from './types';

// Export all types
export type {
  BrandGPTConfig,
  UserRegistration,
  UserLogin,
  User,
  Token,
  ApiKeyResponse,
  SessionCreate,
  Session,
  Document,
  FileIngestionOptions,
  UrlIngestionOptions,
  StructuredDataIngestion,
  IngestionStatus,
  StructuredDataResponse,
  QueryRequest,
  QueryResponse,
  QuerySource,
  PromptCreate,
  Prompt,
  DeleteRequest,
  DeleteResponse,
  ApiError
} from './types';

// Re-export API classes for advanced usage
export { AuthAPI } from './api/auth';
export { SessionsAPI } from './api/sessions';
export { IngestionAPI } from './api/ingestion';
export { QueryAPI } from './api/query';
export { DocumentsAPI } from './api/documents';
export { PromptsAPI } from './api/prompts';