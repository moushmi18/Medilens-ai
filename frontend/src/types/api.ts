export interface ApiError {
  detail: string;
  code?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  hasMore: boolean;
}

export interface HealthResponse {
  status: 'healthy' | 'unhealthy';
  timestamp: string;
}

export interface ReadyResponse {
  status: 'ready' | 'not_ready';
  checks: {
    postgres: boolean;
    redis: boolean;
    qdrant: boolean;
  };
  timestamp: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  fullName?: string;
}

export interface AuthResponse {
  accessToken: string;
  refreshToken: string;
  tokenType: string;
  expiresIn: number;
}

export interface UploadResponse {
  id: string;
  filename: string;
  status: string;
}

export interface ChatRequest {
  message: string;
  conversationId?: string;
  reportId?: string;
}

export interface ChatResponse {
  messageId: string;
  conversationId: string;
  content: string;
  citations: Array<{
    sourceType: string;
    sourceId: string;
    excerpt?: string;
  }>;
}

export interface CompareRequest {
  reportId1: string;
  reportId2: string;
}

export interface CompareResponse {
  reportA: {
    id: string;
    name: string;
    date: string;
  };
  reportB: {
    id: string;
    name: string;
    date: string;
  };
  matchedTests: Array<{
    testName: string;
    valueA: string;
    valueB: string;
    unitA: string;
    unitB: string;
    rangeA?: string;
    rangeB?: string;
  }>;
}

export interface FeedbackRequest {
  messageId?: string;
  feedbackType: 'helpful' | 'not_helpful' | 'incorrect' | 'missing_info';
  comment?: string;
}
