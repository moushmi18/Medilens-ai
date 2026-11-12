import { useState, useEffect } from 'react';
import { 
  FileText, 
  Download, 
  CheckCircle,
  Loader2,
  AlertCircle,
} from 'lucide-react';
import { api } from '../services/api';

interface Report {
  id: string;
  original_filename: string;
  uploaded_at: string;
  status: string;
}

export default function DoctorSummaryPage() {
  const [reports, setReports] = useState<Report[]>([]);
  const [selectedReport, setSelectedReport] = useState<string | null>(null);
  const [includeQuestions, setIncludeQuestions] = useState(true);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    loadReports();
  }, []);

  const loadReports = async () => {
    try {
      const response = await api.listReports(1, 100);
      setReports(response.items.filter((r: Report) => r.status === 'completed'));
    } catch (error) {
      console.error('Failed to load reports:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateSummary = async () => {
    if (!selectedReport) return;

    setGenerating(true);
    setSuccess(false);

    try {
      const response = await fetch(`/api/reports/${selectedReport}/summary`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
        body: JSON.stringify({ include_questions: includeQuestions }),
      });

      if (!response.ok) throw new Error('Failed to generate summary');

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `medilens_summary_${selectedReport}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);

      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
    } catch (error) {
      console.error('Failed to generate summary:', error);
      alert('Failed to generate summary. Please try again.');
    } finally {
      setGenerating(false);
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
    <div className="p-6 max-w-2xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Doctor Summary</h1>
        <p className="text-gray-600 mt-1">
          Generate a PDF summary of your report to share with your healthcare provider
        </p>
      </div>

      <div className="bg-white rounded-lg border p-6 mb-6">
        <h2 className="font-semibold text-gray-900 mb-4">Select a Report</h2>
        
        {reports.length === 0 ? (
          <div className="text-center py-8">
            <FileText className="mx-auto text-gray-300 mb-4" size={48} />
            <p className="text-gray-600">No processed reports available</p>
            <p className="text-sm text-gray-500">Upload and process a report first</p>
          </div>
        ) : (
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {reports.map((report) => (
              <label
                key={report.id}
                className={`flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-colors ${
                  selectedReport === report.id
                    ? 'bg-blue-50 border border-blue-200'
                    : 'bg-gray-50 hover:bg-gray-100'
                }`}
              >
                <input
                  type="radio"
                  name="report"
                  value={report.id}
                  checked={selectedReport === report.id}
                  onChange={() => setSelectedReport(report.id)}
                  className="sr-only"
                />
                <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center ${
                  selectedReport === report.id
                    ? 'border-blue-600'
                    : 'border-gray-300'
                }`}>
                  {selectedReport === report.id && (
                    <div className="w-2.5 h-2.5 rounded-full bg-blue-600" />
                  )}
                </div>
                <div className="flex-1">
                  <p className="font-medium text-gray-900">{report.original_filename}</p>
                  <p className="text-sm text-gray-500">
                    {new Date(report.uploaded_at).toLocaleDateString()}
                  </p>
                </div>
              </label>
            ))}
          </div>
        )}
      </div>

      <div className="bg-white rounded-lg border p-6 mb-6">
        <h2 className="font-semibold text-gray-900 mb-4">Summary Options</h2>
        
        <label className="flex items-start gap-3 cursor-pointer">
          <input
            type="checkbox"
            checked={includeQuestions}
            onChange={(e) => setIncludeQuestions(e.target.checked)}
            className="mt-1 w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
          />
          <div>
            <p className="font-medium text-gray-900">Include patient questions</p>
            <p className="text-sm text-gray-500">
              Add the questions you've asked about this report to help your doctor understand your concerns
            </p>
          </div>
        </label>
      </div>

      <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 mb-6">
        <div className="flex items-start gap-3">
          <AlertCircle className="text-amber-600 flex-shrink-0 mt-0.5" size={20} />
          <div>
            <h3 className="font-semibold text-amber-900">Important Note</h3>
            <p className="text-sm text-amber-800">
              This summary contains extracted lab values and your questions for educational discussion.
              It does NOT include any diagnoses or treatment recommendations.
              Always consult your healthcare provider for medical advice.
            </p>
          </div>
        </div>
      </div>

      <button
        onClick={handleGenerateSummary}
        disabled={!selectedReport || generating}
        className="w-full bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
      >
        {generating ? (
          <>
            <Loader2 size={20} className="animate-spin" />
            Generating PDF...
          </>
        ) : success ? (
          <>
            <CheckCircle size={20} />
            Downloaded Successfully!
          </>
        ) : (
          <>
            <Download size={20} />
            Generate & Download PDF
          </>
        )}
      </button>

      <div className="mt-8 bg-gray-50 rounded-lg p-4">
        <h3 className="font-semibold text-gray-900 mb-2">What's included in the summary?</h3>
        <ul className="text-sm text-gray-600 space-y-1">
          <li>• Report identification and date</li>
          <li>• All extracted lab values with reference ranges</li>
          <li>• Values flagged as outside reference range</li>
          <li>• Your questions about the report (if selected)</li>
          <li>• Educational disclaimer</li>
        </ul>
      </div>
    </div>
  );
}
