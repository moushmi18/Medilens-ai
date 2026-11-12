import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { 
  FileText, 
  ChevronRight, 
  AlertTriangle,
  CheckCircle,
  Info,
  Loader2,
  MessageSquare,
} from 'lucide-react';
import { api } from '../services/api';
import type { Report, ExtractedResult } from '../types/models';

export default function ReportViewerPage() {
  const { id } = useParams<{ id: string }>();
  const [report, setReport] = useState<Report | null>(null);
  const [results, setResults] = useState<ExtractedResult[]>([]);
  const [selectedResult, setSelectedResult] = useState<ExtractedResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (id) {
      loadReport();
    }
  }, [id]);

  const loadReport = async () => {
    try {
      const reportData = await api.getReport(id!);
      setReport(reportData);

      try {
        const resultsData = await api.getReportResults(id!);
        setResults(resultsData.results);
      } catch {
      }
    } catch (error: any) {
      setError(error?.message || 'Failed to load report');
    } finally {
      setLoading(false);
    }
  };

  const handleProcess = async () => {
    setProcessing(true);
    try {
      const resultsData = await api.processReport(id!);
      setResults(resultsData.results);
      setReport(prev => prev ? { ...prev, status: 'completed' } : null);
    } catch (error: any) {
      setError(error?.message || 'Processing failed');
    } finally {
      setProcessing(false);
    }
  };

  const getReferenceRange = (result: ExtractedResult) => {
    if (result.reference_range_low && result.reference_range_high) {
      return `${result.reference_range_low} - ${result.reference_range_high}`;
    }
    return 'N/A';
  };

  const getStatusIndicator = (result: ExtractedResult) => {
    if (result.needs_verification) {
      return (
        <span className="inline-flex items-center gap-1 text-amber-600" title="Needs verification">
          <AlertTriangle size={14} />
        </span>
      );
    }
    if (result.is_abnormal === true) {
      return (
        <span className="inline-flex items-center gap-1 text-red-600" title="Outside reference range">
          <AlertTriangle size={14} />
        </span>
      );
    }
    if (result.is_abnormal === false) {
      return (
        <span className="inline-flex items-center gap-1 text-green-600" title="Within reference range">
          <CheckCircle size={14} />
        </span>
      );
    }
    return null;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="animate-spin text-blue-600" size={32} />
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="flex flex-col items-center justify-center h-full">
        <AlertTriangle className="text-red-500 mb-4" size={48} />
        <h2 className="text-xl font-semibold text-gray-900 mb-2">Error Loading Report</h2>
        <p className="text-gray-600 mb-4">{error || 'Report not found'}</p>
        <Link to="/reports" className="text-blue-600 hover:underline">
          Back to Reports
        </Link>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      <div className="bg-white border-b px-6 py-4">
        <div className="flex items-center gap-2 text-sm text-gray-600 mb-2">
          <Link to="/reports" className="hover:text-blue-600">Reports</Link>
          <ChevronRight size={14} />
          <span className="text-gray-900">{report.original_filename}</span>
        </div>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <FileText className="text-blue-600" size={24} />
            <div>
              <h1 className="text-xl font-semibold text-gray-900">{report.original_filename}</h1>
              <p className="text-sm text-gray-500">
                Uploaded {new Date(report.uploaded_at).toLocaleDateString()}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {results.length > 0 && (
              <Link
                to={`/chat?report=${report.id}`}
                className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
              >
                <MessageSquare size={18} />
                Ask Questions
              </Link>
            )}
            {report.status !== 'completed' && (
              <button
                onClick={handleProcess}
                disabled={processing}
                className="flex items-center gap-2 bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50"
              >
                {processing ? (
                  <>
                    <Loader2 size={18} className="animate-spin" />
                    Processing...
                  </>
                ) : (
                  <>
                    Extract Data
                  </>
                )}
              </button>
            )}
          </div>
        </div>
      </div>

      <div className="flex-1 flex overflow-hidden">
        <div className="w-1/2 border-r bg-gray-100 p-4 overflow-auto">
          <div className="bg-white rounded-lg shadow-sm border p-8 text-center min-h-[400px] flex flex-col items-center justify-center">
            <FileText className="text-gray-300 mb-4" size={64} />
            <h3 className="text-lg font-medium text-gray-700 mb-2">Original Document</h3>
            <p className="text-gray-500 text-sm mb-4">
              Document preview would appear here
            </p>
            <p className="text-xs text-gray-400">
              File type: {report.file_type.toUpperCase()}
            </p>
          </div>
        </div>

        <div className="w-1/2 bg-white overflow-auto">
          <div className="p-4 border-b sticky top-0 bg-white z-10">
            <h2 className="font-semibold text-gray-900">Extracted Results</h2>
            <p className="text-sm text-gray-500">{results.length} values extracted</p>
          </div>

          {results.length === 0 ? (
            <div className="p-8 text-center">
              <Info className="mx-auto text-gray-300 mb-4" size={48} />
              <h3 className="text-lg font-medium text-gray-700 mb-2">No extracted data</h3>
              <p className="text-gray-500 text-sm">
                {report.status === 'completed' 
                  ? 'No lab values were found in this document'
                  : 'Click "Extract Data" to process this report'}
              </p>
            </div>
          ) : (
            <div className="divide-y">
              {results.map((result) => (
                <div
                  key={result.id}
                  className={`p-4 cursor-pointer hover:bg-gray-50 transition-colors ${
                    selectedResult?.id === result.id ? 'bg-blue-50' : ''
                  }`}
                  onClick={() => setSelectedResult(result)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <h3 className="font-medium text-gray-900">{result.test_name}</h3>
                        {getStatusIndicator(result)}
                      </div>
                      <div className="flex items-baseline gap-2 mt-1">
                        <span className="text-2xl font-semibold text-gray-900">
                          {result.observed_value || 'N/A'}
                        </span>
                        {result.unit && (
                          <span className="text-gray-500">{result.unit}</span>
                        )}
                      </div>
                      <p className="text-sm text-gray-500 mt-1">
                        Reference: {getReferenceRange(result)}
                      </p>
                      {result.needs_verification && (
                        <p className="text-xs text-amber-600 mt-1 flex items-center gap-1">
                          <AlertTriangle size={12} />
                          Low confidence - please verify this value
                        </p>
                      )}
                    </div>
                    {result.confidence_score != null && (
                      <div className="text-right">
                        <span className={`text-xs px-2 py-1 rounded-full ${
                          (result.confidence_score ?? 0) >= 0.8 
                            ? 'bg-green-100 text-green-700'
                            : (result.confidence_score ?? 0) >= 0.5
                            ? 'bg-amber-100 text-amber-700'
                            : 'bg-red-100 text-red-700'
                        }`}>
                          {Math.round((result.confidence_score ?? 0) * 100)}% confidence
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {selectedResult && (
        <div className="border-t bg-white p-4">
          <div className="flex items-start justify-between">
            <div>
              <h3 className="font-semibold text-gray-900">{selectedResult.test_name}</h3>
              <p className="text-sm text-gray-600 mt-1">
                Click "Ask Questions" above to learn more about this test and what your results mean.
              </p>
            </div>
            <button
              onClick={() => setSelectedResult(null)}
              className="text-gray-400 hover:text-gray-600"
            >
              ×
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
