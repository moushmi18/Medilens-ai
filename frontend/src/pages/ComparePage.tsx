import { useState, useEffect } from 'react';
import { 
  GitCompare, 
  Check, 
  ArrowUp, 
  ArrowDown, 
  Minus,
  Loader2,
  AlertCircle,
} from 'lucide-react';
import { api } from '../services/api';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';

interface Report {
  id: string;
  original_filename: string;
  uploaded_at: string;
}

interface Comparison {
  test_name: string;
  reports: {
    report_id: string;
    value: string | null;
    unit: string | null;
    is_abnormal: boolean | null;
    reference_range: string | null;
  }[];
  change: number | null;
  change_direction: string | null;
  unit: string | null;
}

interface ComparisonResult {
  report_ids: string[];
  report_dates: string[];
  comparisons: Comparison[];
  matched_tests: number;
  unmatched_tests: number;
}

export default function ComparePage() {
  const [reports, setReports] = useState<Report[]>([]);
  const [selectedReports, setSelectedReports] = useState<string[]>([]);
  const [comparison, setComparison] = useState<ComparisonResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [comparing, setComparing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadReports();
  }, []);

  const loadReports = async () => {
    try {
      const response = await api.listReports(1, 100);
      setReports(response.items.filter((r: Report) => r.uploaded_at));
    } catch (error) {
      console.error('Failed to load reports:', error);
    } finally {
      setLoading(false);
    }
  };

  const toggleReport = (reportId: string) => {
    setSelectedReports(prev => {
      if (prev.includes(reportId)) {
        return prev.filter(id => id !== reportId);
      }
      return [...prev, reportId];
    });
    setComparison(null);
  };

  const handleCompare = async () => {
    if (selectedReports.length < 2) {
      setError('Please select at least 2 reports to compare');
      return;
    }

    setComparing(true);
    setError(null);

    try {
      const result = await api.compareReports(selectedReports) as unknown as ComparisonResult;
      setComparison(result);
    } catch (error: any) {
      setError(error?.message || 'Comparison failed');
    } finally {
      setComparing(false);
    }
  };

  const getChangeIcon = (direction: string | null) => {
    switch (direction) {
      case 'increased':
        return <ArrowUp className="text-red-500" size={16} />;
      case 'decreased':
        return <ArrowDown className="text-blue-500" size={16} />;
      default:
        return <Minus className="text-gray-400" size={16} />;
    }
  };

  const getChartData = () => {
    if (!comparison) return [];

    return comparison.comparisons
      .filter(c => c.reports.every(r => r.value !== null))
      .slice(0, 5)
      .map(c => {
        const data: any = { name: c.test_name };
        c.reports.forEach((r, i) => {
          const report = reports.find(rep => rep.id === r.report_id);
          const label = report 
            ? new Date(report.uploaded_at).toLocaleDateString() 
            : `Report ${i + 1}`;
          data[label] = parseFloat(r.value || '0');
        });
        return data;
      });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="animate-spin text-blue-600" size={32} />
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Compare Reports</h1>
        <p className="text-gray-600">Select multiple reports to compare lab values over time</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1">
          <div className="bg-white rounded-lg border p-4">
            <h2 className="font-semibold text-gray-900 mb-4">Select Reports</h2>
            
            {reports.length === 0 ? (
              <p className="text-gray-500 text-sm">No reports available</p>
            ) : (
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {reports.map((report) => (
                  <label
                    key={report.id}
                    className={`flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-colors ${
                      selectedReports.includes(report.id)
                        ? 'bg-blue-50 border border-blue-200'
                        : 'bg-gray-50 hover:bg-gray-100'
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={selectedReports.includes(report.id)}
                      onChange={() => toggleReport(report.id)}
                      className="sr-only"
                    />
                    <div className={`w-5 h-5 rounded border-2 flex items-center justify-center ${
                      selectedReports.includes(report.id)
                        ? 'bg-blue-600 border-blue-600'
                        : 'border-gray-300'
                    }`}>
                      {selectedReports.includes(report.id) && (
                        <Check className="text-white" size={14} />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {report.original_filename}
                      </p>
                      <p className="text-xs text-gray-500">
                        {new Date(report.uploaded_at).toLocaleDateString()}
                      </p>
                    </div>
                  </label>
                ))}
              </div>
            )}

            <button
              onClick={handleCompare}
              disabled={selectedReports.length < 2 || comparing}
              className="w-full mt-4 bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {comparing ? (
                <>
                  <Loader2 size={18} className="animate-spin" />
                  Comparing...
                </>
              ) : (
                <>
                  <GitCompare size={18} />
                  Compare ({selectedReports.length} selected)
                </>
              )}
            </button>

            {error && (
              <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2 text-red-700 text-sm">
                <AlertCircle size={16} />
                {error}
              </div>
            )}
          </div>
        </div>

        <div className="lg:col-span-2">
          {comparison ? (
            <div className="space-y-6">
              <div className="bg-white rounded-lg border p-4">
                <h2 className="font-semibold text-gray-900 mb-4">Comparison Chart</h2>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={getChartData()}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                      <YAxis tick={{ fontSize: 12 }} />
                      <Tooltip />
                      <Legend />
                      {comparison.report_ids.map((_, i) => {
                        const report = reports.find(r => r.id === comparison.report_ids[i]);
                        const key = report 
                          ? new Date(report.uploaded_at).toLocaleDateString()
                          : `Report ${i + 1}`;
                        const colors = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444'];
                        return (
                          <Line
                            key={i}
                            type="monotone"
                            dataKey={key}
                            stroke={colors[i % colors.length]}
                            strokeWidth={2}
                          />
                        );
                      })}
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>

              <div className="bg-white rounded-lg border overflow-hidden">
                <div className="p-4 border-b">
                  <h2 className="font-semibold text-gray-900">Detailed Comparison</h2>
                  <p className="text-sm text-gray-500">
                    {comparison.matched_tests} tests matched, {comparison.unmatched_tests} unmatched
                  </p>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-gray-50 border-b">
                      <tr>
                        <th className="text-left px-4 py-3 text-sm font-medium text-gray-600">Test</th>
                        {comparison.report_ids.map((id, i) => {
                          const report = reports.find(r => r.id === id);
                          return (
                            <th key={id} className="text-left px-4 py-3 text-sm font-medium text-gray-600">
                              {report 
                                ? new Date(report.uploaded_at).toLocaleDateString()
                                : `Report ${i + 1}`}
                            </th>
                          );
                        })}
                        <th className="text-left px-4 py-3 text-sm font-medium text-gray-600">Change</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y">
                      {comparison.comparisons.map((comp, i) => (
                        <tr key={i} className="hover:bg-gray-50">
                          <td className="px-4 py-3 font-medium text-gray-900">
                            {comp.test_name}
                          </td>
                          {comp.reports.map((r, j) => (
                            <td key={j} className="px-4 py-3">
                              <span className={`${
                                r.is_abnormal === true ? 'text-red-600 font-medium' : 'text-gray-900'
                              }`}>
                                {r.value || '-'} {r.unit || ''}
                              </span>
                              {r.reference_range && (
                                <p className="text-xs text-gray-500">Ref: {r.reference_range}</p>
                              )}
                            </td>
                          ))}
                          <td className="px-4 py-3">
                            <div className="flex items-center gap-1">
                              {getChangeIcon(comp.change_direction)}
                              {comp.change !== null && (
                                <span className={`text-sm ${
                                  comp.change_direction === 'increased' ? 'text-red-600' :
                                  comp.change_direction === 'decreased' ? 'text-blue-600' :
                                  'text-gray-600'
                                }`}>
                                  {comp.change > 0 ? '+' : ''}{comp.change.toFixed(1)}
                                </span>
                              )}
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-white rounded-lg border p-8 text-center">
              <GitCompare className="mx-auto text-gray-300 mb-4" size={48} />
              <h3 className="text-lg font-medium text-gray-700 mb-2">Select Reports to Compare</h3>
              <p className="text-gray-500 text-sm">
                Choose at least 2 reports from the list to see how your values have changed over time.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
