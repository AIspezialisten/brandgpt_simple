import { HttpClient } from '../http-client';
import { 
  UserRegistration, 
  UserLogin, 
  User, 
  Token, 
  ApiKeyResponse 
} from '../types';

export class AuthAPI {
  constructor(private client: HttpClient) {}

  /**
   * Register a new user
   */
  async register(userData: UserRegistration): Promise<User> {
    return this.client.post<User>('/api/auth/register', userData);
  }

  /**
   * Login and get JWT token
   */
  async login(credentials: UserLogin): Promise<Token> {
    const formData = new URLSearchParams();
    formData.append('username', credentials.username);
    formData.append('password', credentials.password);

    return this.client.post<Token>('/api/auth/token', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
  }

  /**
   * Generate an API key for the current user
   */
  async generateApiKey(): Promise<ApiKeyResponse> {
    return this.client.post<ApiKeyResponse>('/api/auth/api-key');
  }

  /**
   * Get current user information
   */
  async getCurrentUser(): Promise<User> {
    return this.client.get<User>('/api/auth/me');
  }
}