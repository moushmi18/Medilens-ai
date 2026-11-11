export interface User {
  id: string;
  email: string;
  fullName?: string;
  createdAt: string;
  emailVerified: boolean;
}

export interface Report {
  id: string;
  filename: string;
  originalFilename: string;
  fileType: string;
  fileSize: number;
  status: 'uploaded' | 'processing' | 'completed' | 'failed';
  processingError?: string;
  reportDate?: string;
  labName?: string;
  patientName?: string;
  pageCount?: number;
  ocrRequired: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface ExtractedResult {
  id: string;
  reportId: string;
  testName: string;
  observedValue?: string;
  unit?: string;
  referenceRangeLow?: string;
  referenceRangeHigh?: string;
  referenceRangeText?: string;
  isAbnormal?: boolean;
  pageNumber?: number;
  confidenceScore?: number;
  needsVerification: boolean;
  verificationNote?: string;
}

export interface Conversation {
  id: string;
  title?: string;
  reportId?: string;
  createdAt: string;
  updatedAt: string;
}

export interface Message {
  id: string;
  conversationId: string;
  role: 'user' | 'assistant';
  content: string;
  intentClassification?: string;
  safetyFlags?: Record<string, unknown>;
  createdAt: string;
}

export interface Citation {
  id: string;
  messageId: string;
  sourceType: 'report' | 'knowledge';
  sourceId: string;
  chunkId?: string;
  excerpt?: string;
  relevanceScore?: number;
}

export interface KnowledgeSource {
  id: string;
  title: string;
  publisher: string;
  url: string;
  publicationDate?: string;
  retrievalDate: string;
  topic?: string;
  verificationStatus: 'pending' | 'verified' | 'rejected';
  isActive: boolean;
}

export interface DashboardStats {
  totalReports: number;
  processedReports: number;
  processingReports: number;
  recentReports: Report[];
  recentConversations: Conversation[];
}
