import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import FormData from 'form-data';
import { BrandGPTConfig, BrandGPTError } from './types';

export class HttpClient {
  private client: AxiosInstance;
  private apiKey?: string;

  constructor(config: BrandGPTConfig) {
    this.apiKey = config.apiKey;
    
    this.client = axios.create({
      baseURL: config.baseUrl,
      timeout: config.timeout || 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor to add authentication
    this.client.interceptors.request.use((config) => {
      if (this.apiKey) {
        config.headers.Authorization = `Bearer ${this.apiKey}`;
      }
      return config;
    });

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response) {
          const { status, data } = error.response;
          throw new BrandGPTError(
            data?.detail || error.message,
            status,
            data
          );
        }
        throw new BrandGPTError(error.message);
      }
    );
  }

  setApiKey(apiKey: string): void {
    this.apiKey = apiKey;
  }

  async get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response: AxiosResponse<T> = await this.client.get(url, config);
    return response.data;
  }

  async post<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response: AxiosResponse<T> = await this.client.post(url, data, config);
    return response.data;
  }

  async put<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response: AxiosResponse<T> = await this.client.put(url, data, config);
    return response.data;
  }

  async delete<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response: AxiosResponse<T> = await this.client.delete(url, config);
    return response.data;
  }

  async uploadFile<T>(
    url: string,
    file: Buffer | NodeJS.ReadableStream,
    filename: string,
    additionalFields?: Record<string, string>
  ): Promise<T> {
    const formData = new FormData();
    formData.append('file', file, filename);
    
    if (additionalFields) {
      Object.entries(additionalFields).forEach(([key, value]) => {
        formData.append(key, value);
      });
    }

    const response: AxiosResponse<T> = await this.client.post(url, formData, {
      headers: {
        ...formData.getHeaders(),
        Authorization: this.apiKey ? `Bearer ${this.apiKey}` : undefined,
      },
    });

    return response.data;
  }
}