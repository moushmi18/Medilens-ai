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
  original_filename: string;
  file_type: string;
  file_size?: number;
  status: 'uploaded' | 'processing' | 'completed' | 'failed';
  processing_error?: string;
  uploaded_at: string;
  report_date?: string;
  lab_name?: string;
  patient_name?: string;
  page_count?: number;
  ocr_required?: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface ExtractedResult {
  id: string;
  report_id: string;
  test_name: string;
  observed_value?: string | null;
  unit?: string | null;
  reference_range_low?: string | null;
  reference_range_high?: string | null;
  reference_range_text?: string | null;
  is_abnormal?: boolean | null;
  page_number?: number | null;
  confidence_score?: number | null;
  needs_verification: boolean;
  verification_note?: string | null;
}

export interface Conversation {
  id: string;
  title?: string;
  report_id?: string;
  created_at: string;
  updated_at: string;
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
