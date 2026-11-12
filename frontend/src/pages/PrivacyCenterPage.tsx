import { useState, useEffect } from 'react';
import { 
  Shield, 
  Trash2, 
  AlertTriangle,
  FileText,
  MessageSquare,
  Loader2,
  Clock,
} from 'lucide-react';
import { api } from '../services/api';

interface Stats {
  total_reports: number;
  total_conversations: number;
}

export default function PrivacyCenterPage() {
  const [stats, setStats] = useState<Stats>({ total_reports: 0, total_conversations: 0 });
  const [loading, setLoading] = useState(true);
  const [deletingReports, setDeletingReports] = useState(false);
  const [deletingConversations, setDeletingConversations] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState<'reports' | 'conversations' | 'all' | null>(null);
  const [retentionDays, setRetentionDays] = useState(90);

  const [savingRetention, setSavingRetention] = useState(false);
  const [retentionSaved, setRetentionSaved] = useState(false);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      const reportsResponse = await api.listReports(1, 1);
      setStats(prev => ({ ...prev, total_reports: reportsResponse.total }));
      
      try {
        const convsResponse = await api.listConversations(1, 1);
        setStats(prev => ({ ...prev, total_conversations: convsResponse.total }));
      } catch {}

      try {
        const retention = await api.getRetention();
        setRetentionDays(retention.retention_days);
      } catch {}
    } catch (error) {
      console.error('Failed to load stats:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveRetention = async (days: number) => {
    setRetentionDays(days);
    setSavingRetention(true);
    try {
      await api.updateRetention(days);
      setRetentionSaved(true);
      setTimeout(() => setRetentionSaved(false), 2000);
    } catch (error) {
      console.error('Failed to save retention:', error);
      alert('Failed to save retention setting.');
    } finally {
      setSavingRetention(false);
    }
  };

  const handleDeleteAllReports = async () => {
    setDeletingReports(true);
    try {
      const response = await api.listReports(1, 100);
      for (const report of response.items) {
        await api.deleteReport(report.id);
      }
      setStats(prev => ({ ...prev, total_reports: 0 }));
      setConfirmDelete(null);
    } catch (error) {
      console.error('Failed to delete reports:', error);
      alert('Failed to delete some reports. Please try again.');
    } finally {
      setDeletingReports(false);
    }
  };

  const handleDeleteAllConversations = async () => {
    setDeletingConversations(true);
    try {
      const response = await api.listConversations(1, 100);
      for (const conv of response.items) {
        await api.deleteConversation(conv.id);
      }
      setStats(prev => ({ ...prev, total_conversations: 0 }));
      setConfirmDelete(null);
    } catch (error) {
      console.error('Failed to delete conversations:', error);
      alert('Failed to delete some conversations. Please try again.');
    } finally {
      setDeletingConversations(false);
    }
  };

  const handleDeleteAll = async () => {
    await handleDeleteAllReports();
    await handleDeleteAllConversations();
    setConfirmDelete(null);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="animate-spin text-blue-600" size={32} />
      </div>
    );
  }

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-2">
          <Shield className="text-blue-600" size={28} />
          <h1 className="text-2xl font-bold text-gray-900">Privacy Center</h1>
        </div>
        <p className="text-gray-600">
          Manage your data and privacy settings. Delete your reports and conversation history.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
        <div className="bg-white rounded-lg border p-5">
          <div className="flex items-center gap-3 mb-2">
            <FileText className="text-blue-600" size={24} />
            <div>
              <p className="text-2xl font-bold text-gray-900">{stats.total_reports}</p>
              <p className="text-sm text-gray-600">Reports Stored</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-lg border p-5">
          <div className="flex items-center gap-3 mb-2">
            <MessageSquare className="text-purple-600" size={24} />
            <div>
              <p className="text-2xl font-bold text-gray-900">{stats.total_conversations}</p>
              <p className="text-sm text-gray-600">Conversations</p>
            </div>
          </div>
        </div>
      </div>

      <div className="space-y-4">
        <div className="bg-white rounded-lg border p-6">
          <h2 className="font-semibold text-gray-900 mb-4">Data Retention</h2>
          <div className="flex items-center gap-4">
            <Clock className="text-gray-400" size={20} />
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Auto-delete data after
              </label>
              <select
                value={retentionDays}
                onChange={(e) => handleSaveRetention(Number(e.target.value))}
                disabled={savingRetention}
                className="border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value={30}>30 days</option>
                <option value={90}>90 days</option>
                <option value={180}>180 days</option>
                <option value={365}>1 year</option>
                <option value={0}>Never (manual only)</option>
              </select>
            </div>
          </div>
          <p className="text-sm text-gray-500 mt-2">
            Preference saved to your account{retentionSaved ? ' ✓' : ''}. Automatic purge jobs are not scheduled in this educational build — use manual deletion below.
          </p>
        </div>

        <div className="bg-white rounded-lg border p-6">
          <h2 className="font-semibold text-gray-900 mb-4">Delete Reports</h2>
          <p className="text-gray-600 text-sm mb-4">
            Delete all your uploaded medical reports and their extracted data.
            This also removes all vector embeddings from the search index.
          </p>
          
          {confirmDelete === 'reports' ? (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex items-start gap-3">
                <AlertTriangle className="text-red-600 flex-shrink-0" size={20} />
                <div>
                  <p className="font-medium text-red-900">Are you sure?</p>
                  <p className="text-sm text-red-700 mb-3">
                    This will permanently delete {stats.total_reports} report(s) and cannot be undone.
                  </p>
                  <div className="flex gap-2">
                    <button
                      onClick={handleDeleteAllReports}
                      disabled={deletingReports}
                      className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 disabled:opacity-50 flex items-center gap-2"
                    >
                      {deletingReports ? (
                        <>
                          <Loader2 size={16} className="animate-spin" />
                          Deleting...
                        </>
                      ) : (
                        'Yes, Delete All'
                      )}
                    </button>
                    <button
                      onClick={() => setConfirmDelete(null)}
                      className="px-4 py-2 border rounded-lg hover:bg-gray-50"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <button
              onClick={() => setConfirmDelete('reports')}
              disabled={stats.total_reports === 0}
              className="flex items-center gap-2 text-red-600 hover:text-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Trash2 size={18} />
              Delete All Reports ({stats.total_reports})
            </button>
          )}
        </div>

        <div className="bg-white rounded-lg border p-6">
          <h2 className="font-semibold text-gray-900 mb-4">Delete Conversations</h2>
          <p className="text-gray-600 text-sm mb-4">
            Delete all your chat conversations and message history.
          </p>
          
          {confirmDelete === 'conversations' ? (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex items-start gap-3">
                <AlertTriangle className="text-red-600 flex-shrink-0" size={20} />
                <div>
                  <p className="font-medium text-red-900">Are you sure?</p>
                  <p className="text-sm text-red-700 mb-3">
                    This will permanently delete {stats.total_conversations} conversation(s).
                  </p>
                  <div className="flex gap-2">
                    <button
                      onClick={handleDeleteAllConversations}
                      disabled={deletingConversations}
                      className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 disabled:opacity-50 flex items-center gap-2"
                    >
                      {deletingConversations ? (
                        <>
                          <Loader2 size={16} className="animate-spin" />
                          Deleting...
                        </>
                      ) : (
                        'Yes, Delete All'
                      )}
                    </button>
                    <button
                      onClick={() => setConfirmDelete(null)}
                      className="px-4 py-2 border rounded-lg hover:bg-gray-50"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <button
              onClick={() => setConfirmDelete('conversations')}
              disabled={stats.total_conversations === 0}
              className="flex items-center gap-2 text-red-600 hover:text-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Trash2 size={18} />
              Delete All Conversations ({stats.total_conversations})
            </button>
          )}
        </div>

        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <h2 className="font-semibold text-red-900 mb-4">Delete All Data</h2>
          <p className="text-red-800 text-sm mb-4">
            Delete all your data including reports, conversations, and any associated information.
            This action cannot be undone.
          </p>
          
          {confirmDelete === 'all' ? (
            <div className="bg-white border border-red-300 rounded-lg p-4">
              <div className="flex items-start gap-3">
                <AlertTriangle className="text-red-600 flex-shrink-0" size={20} />
                <div>
                  <p className="font-medium text-red-900">Final Warning</p>
                  <p className="text-sm text-red-700 mb-3">
                    This will permanently delete ALL your data. Are you absolutely sure?
                  </p>
                  <div className="flex gap-2">
                    <button
                      onClick={handleDeleteAll}
                      disabled={deletingReports || deletingConversations}
                      className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 disabled:opacity-50 flex items-center gap-2"
                    >
                      {(deletingReports || deletingConversations) ? (
                        <>
                          <Loader2 size={16} className="animate-spin" />
                          Deleting Everything...
                        </>
                      ) : (
                        'Yes, Delete Everything'
                      )}
                    </button>
                    <button
                      onClick={() => setConfirmDelete(null)}
                      className="px-4 py-2 border rounded-lg hover:bg-gray-50"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <button
              onClick={() => setConfirmDelete('all')}
              disabled={stats.total_reports === 0 && stats.total_conversations === 0}
              className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              <Trash2 size={18} />
              Delete All My Data
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
