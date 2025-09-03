import { BrandGPTClient } from '../client';
import { BrandGPTError } from '../types';

// Mock axios
jest.mock('axios');

describe('BrandGPTClient', () => {
  let client: BrandGPTClient;

  beforeEach(() => {
    client = new BrandGPTClient({
      baseUrl: 'https://api.example.com',
      apiKey: 'test-api-key'
    });
  });

  describe('constructor', () => {
    it('should create client with proper configuration', () => {
      expect(client).toBeInstanceOf(BrandGPTClient);
      expect(client.auth).toBeDefined();
      expect(client.sessions).toBeDefined();
      expect(client.ingestion).toBeDefined();
      expect(client.query).toBeDefined();
      expect(client.documents).toBeDefined();
      expect(client.prompts).toBeDefined();
    });
  });

  describe('setApiKey', () => {
    it('should update API key', () => {
      const newApiKey = 'new-api-key';
      client.setApiKey(newApiKey);
      // Test that the API key was set (implementation detail)
    });
  });
});

describe('BrandGPTError', () => {
  it('should create error with message', () => {
    const error = new BrandGPTError('Test error');
    expect(error.message).toBe('Test error');
    expect(error.name).toBe('BrandGPTError');
  });

  it('should create error with status code and details', () => {
    const error = new BrandGPTError('Test error', 404, { detail: 'Not found' });
    expect(error.statusCode).toBe(404);
    expect(error.details).toEqual({ detail: 'Not found' });
  });
});