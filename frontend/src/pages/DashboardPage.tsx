import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  FileText, 
  MessageSquare, 
  Upload, 
  Clock,
  CheckCircle,
  AlertCircle,
  Loader2,
  ArrowRight,
} from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { api } from '../services/api';

interface Report {
  id: string;
  filename: string;
  original_filename: string;
  status: string;
  uploaded_at: string;
}

interface Conversation {
  id: string;
  title?: string;
  updated_at: string;
}

interface DashboardStats {
  total_reports: number;
  processed_reports: number;
  processing_reports: number;
  total_conversations: number;
}

export default function DashboardPage() {
  const { user } = useAuth();
  const [stats, setStats] = useState<DashboardStats>({
    total_reports: 0,
    processed_reports: 0,
    processing_reports: 0,
    total_conversations: 0,
  });
  const [recentReports, setRecentReports] = useState<Report[]>([]);
  const [recentConversations, setRecentConversations] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      const reportsResponse = await api.listReports(1, 5);
      setRecentReports(reportsResponse.items);
      
      const processed = reportsResponse.items.filter((r: Report) => r.status === 'completed').length;
      const processing = reportsResponse.items.filter((r: Report) => r.status === 'processing').length;
      
      setStats({
        total_reports: reportsResponse.total,
        processed_reports: processed,
        processing_reports: processing,
        total_conversations: 0,
      });

      try {
        const convsResponse = await api.listConversations(1, 5);
        setRecentConversations(convsResponse.items);
        setStats(prev => ({ ...prev, total_conversations: convsResponse.total }));
      } catch {
      }
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="text-green-500" size={16} />;
      case 'processing':
        return <Loader2 className="text-blue-500 animate-spin" size={16} />;
      case 'failed':
        return <AlertCircle className="text-red-500" size={16} />;
      default:
        return <Clock className="text-gray-400" size={16} />;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="animate-spin text-blue-600" size={32} />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-600">Welcome back{user?.email ? `, ${user.email.split('@')[0]}` : ''}!</p>
        </div>
        <Link
          to="/upload"
          className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
        >
          <Upload size={18} />
          Upload Report
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg border p-5">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
              <FileText className="text-blue-600" size={20} />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">{stats.total_reports}</p>
              <p className="text-sm text-gray-600">Total Reports</p>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-lg border p-5">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
              <CheckCircle className="text-green-600" size={20} />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">{stats.processed_reports}</p>
              <p className="text-sm text-gray-600">Processed</p>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-lg border p-5">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-amber-100 rounded-lg flex items-center justify-center">
              <Loader2 className="text-amber-600" size={20} />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">{stats.processing_reports}</p>
              <p className="text-sm text-gray-600">Processing</p>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-lg border p-5">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
              <MessageSquare className="text-purple-600" size={20} />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">{stats.total_conversations}</p>
              <p className="text-sm text-gray-600">Conversations</p>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg border">
          <div className="p-4 border-b flex items-center justify-between">
            <h2 className="font-semibold text-gray-900">Recent Reports</h2>
            <Link to="/reports" className="text-blue-600 text-sm hover:underline flex items-center gap-1">
              View all <ArrowRight size={14} />
            </Link>
          </div>
          <div className="p-4">
            {recentReports.length === 0 ? (
              <div className="text-center py-8">
                <FileText className="mx-auto text-gray-300 mb-3" size={40} />
                <p className="text-gray-600">No reports yet</p>
                <Link to="/upload" className="text-blue-600 text-sm hover:underline">
                  Upload your first report
                </Link>
              </div>
            ) : (
              <ul className="space-y-3">
                {recentReports.map((report) => (
                  <li key={report.id}>
                    <Link
                      to={`/reports/${report.id}`}
                      className="flex items-center justify-between p-3 rounded-lg hover:bg-gray-50 transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        {getStatusIcon(report.status)}
                        <div>
                          <p className="font-medium text-gray-900 text-sm">
                            {report.original_filename}
                          </p>
                          <p className="text-xs text-gray-500">
                            {new Date(report.uploaded_at).toLocaleDateString()}
                          </p>
                        </div>
                      </div>
                      <ArrowRight className="text-gray-400" size={16} />
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>

        <div className="bg-white rounded-lg border">
          <div className="p-4 border-b flex items-center justify-between">
            <h2 className="font-semibold text-gray-900">Recent Conversations</h2>
            <Link to="/chat" className="text-blue-600 text-sm hover:underline flex items-center gap-1">
              New chat <ArrowRight size={14} />
            </Link>
          </div>
          <div className="p-4">
            {recentConversations.length === 0 ? (
              <div className="text-center py-8">
                <MessageSquare className="mx-auto text-gray-300 mb-3" size={40} />
                <p className="text-gray-600">No conversations yet</p>
                <Link to="/chat" className="text-blue-600 text-sm hover:underline">
                  Start asking questions
                </Link>
              </div>
            ) : (
              <ul className="space-y-3">
                {recentConversations.map((conv) => (
                  <li key={conv.id}>
                    <Link
                      to={`/chat?conversation=${conv.id}`}
                      className="flex items-center justify-between p-3 rounded-lg hover:bg-gray-50 transition-colors"
                    >
                      <div>
                        <p className="font-medium text-gray-900 text-sm truncate max-w-xs">
                          {conv.title || 'Untitled conversation'}
                        </p>
                        <p className="text-xs text-gray-500">
                          {new Date(conv.updated_at).toLocaleDateString()}
                        </p>
                      </div>
                      <ArrowRight className="text-gray-400" size={16} />
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </div>

      <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <AlertCircle className="text-amber-600 flex-shrink-0 mt-0.5" size={20} />
          <div>
            <h3 className="font-semibold text-amber-900">Educational Use Only</h3>
            <p className="text-sm text-amber-800">
              MediLens AI provides educational information about medical reports.
              Always consult your healthcare provider for medical advice, diagnosis, or treatment.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
