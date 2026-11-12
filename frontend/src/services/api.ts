import axios from 'axios';
import type { AxiosError, AxiosInstance, AxiosRequestConfig, InternalAxiosRequestConfig } from 'axios';
import type {
  HealthResponse,
  ReadyResponse,
  LoginRequest,
  RegisterRequest,
  AuthResponse,
  UploadResponse,
  ChatRequest,
  ChatResponse,
  CompareResponse,
  FeedbackRequest,
  PaginatedResponse,
  ApiError,
} from '../types/api';
import type {
  User,
  Report,
  ExtractedResult,
  Conversation,
  Message,
  KnowledgeSource,
  DashboardStats,
} from '../types/models';

const API_BASE_URL = '/api';

class ApiClient {
  private client: AxiosInstance;
  private accessToken: string | null = null;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.client.interceptors.request.use((config: InternalAxiosRequestConfig) => {
      if (this.accessToken && config.headers) {
        config.headers.Authorization = `Bearer ${this.accessToken}`;
      }
      return config;
    });

    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError<ApiError>) => {
        if (error.response?.status === 401) {
          this.accessToken = null;
          localStorage.removeItem('accessToken');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );

    const storedToken = localStorage.getItem('accessToken');
    if (storedToken) {
      this.accessToken = storedToken;
    }
  }

  setAccessToken(token: string | null) {
    this.accessToken = token;
    if (token) {
      localStorage.setItem('accessToken', token);
    } else {
      localStorage.removeItem('accessToken');
    }
  }

  getAccessToken(): string | null {
    return this.accessToken;
  }

  async health(): Promise<HealthResponse> {
    const { data } = await this.client.get<HealthResponse>('/health');
    return data;
  }

  async ready(): Promise<ReadyResponse> {
    const { data } = await this.client.get<ReadyResponse>('/health/ready');
    return data;
  }

  async register(request: RegisterRequest): Promise<AuthResponse> {
    const { data } = await this.client.post<AuthResponse>('/auth/register', request);
    this.setAccessToken(data.accessToken);
    return data;
  }

  async login(request: LoginRequest): Promise<AuthResponse> {
    const { data } = await this.client.post<AuthResponse>('/auth/login', request);
    this.setAccessToken(data.accessToken);
    return data;
  }

  async logout(): Promise<void> {
    try {
      await this.client.post('/auth/logout');
    } finally {
      this.setAccessToken(null);
    }
  }

  async getMe(): Promise<User> {
    const { data } = await this.client.get<User>('/auth/me');
    return data;
  }

  async getDashboard(): Promise<DashboardStats> {
    const { data } = await this.client.get<DashboardStats>('/dashboard');
    return data;
  }

  async uploadReport(file: File, onProgress?: (progress: number) => void): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const config: AxiosRequestConfig = {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (progressEvent.total && onProgress) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(progress);
        }
      },
    };

    const { data } = await this.client.post<UploadResponse>('/reports/upload', formData, config);
    return data;
  }

  async listReports(page = 1, pageSize = 10): Promise<PaginatedResponse<Report>> {
    const { data } = await this.client.get<PaginatedResponse<Report>>('/reports', {
      params: { page, page_size: pageSize },
    });
    return data;
  }

  async getReports(page = 1, pageSize = 10): Promise<PaginatedResponse<Report>> {
    return this.listReports(page, pageSize);
  }

  async getReport(id: string): Promise<Report> {
    const { data } = await this.client.get<Report>(`/reports/${id}`);
    return data;
  }

  async getReportStatus(id: string): Promise<{ status: string; error?: string }> {
    const { data } = await this.client.get<{ status: string; error?: string }>(`/reports/${id}/status`);
    return data;
  }

  async getReportResults(id: string): Promise<{ results: ExtractedResult[]; total: number }> {
    const { data } = await this.client.get<{ results: ExtractedResult[]; total: number }>(`/reports/${id}/results`);
    return data;
  }

  async processReport(id: string): Promise<{ results: ExtractedResult[]; total: number }> {
    const { data } = await this.client.post<{ results: ExtractedResult[]; total: number }>(`/reports/${id}/process`);
    return data;
  }

  async deleteReport(id: string): Promise<void> {
    await this.client.delete(`/reports/${id}`);
  }

  async chat(request: ChatRequest): Promise<ChatResponse> {
    const { data } = await this.client.post<ChatResponse>('/chat', request);
    return data;
  }

  async listConversations(page = 1, pageSize = 10): Promise<PaginatedResponse<Conversation>> {
    const { data } = await this.client.get<PaginatedResponse<Conversation>>('/chat/conversations', {
      params: { page, page_size: pageSize },
    });
    return data;
  }

  async getConversations(page = 1, pageSize = 10): Promise<PaginatedResponse<Conversation>> {
    return this.listConversations(page, pageSize);
  }

  async getConversation(id: string): Promise<{ conversation: Conversation; messages: Message[] }> {
    const { data } = await this.client.get<{ conversation: Conversation; messages: Message[] }>(
      `/chat/conversations/${id}`
    );
    return data;
  }

  async deleteConversation(id: string): Promise<void> {
    await this.client.delete(`/chat/conversations/${id}`);
  }

  async compareReports(reportIds: string[]): Promise<CompareResponse> {
    const { data } = await this.client.post<CompareResponse>('/reports/compare', { report_ids: reportIds });
    return data;
  }

  async generateDoctorSummary(reportId: string): Promise<Blob> {
    const { data } = await this.client.post(
      '/doctor-summary',
      { reportId },
      { responseType: 'blob' }
    );
    return data;
  }

  async getSources(page = 1, pageSize = 20): Promise<PaginatedResponse<KnowledgeSource>> {
    const { data } = await this.client.get<PaginatedResponse<KnowledgeSource>>('/sources', {
      params: { page, page_size: pageSize },
    });
    return data;
  }

  async submitFeedback(request: FeedbackRequest): Promise<void> {
    await this.client.post('/feedback', request);
  }
}

export const api = new ApiClient();
export default api;
