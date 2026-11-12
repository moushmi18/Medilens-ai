import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Upload, 
  X, 
  CheckCircle, 
  AlertCircle, 
  FileText,
  Image as ImageIcon,
} from 'lucide-react';
import { api } from '../services/api';

const ALLOWED_TYPES = [
  'application/pdf',
  'image/png',
  'image/jpeg',
  'image/jpg',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
];

const MAX_SIZE_MB = 50;

interface UploadState {
  file: File | null;
  progress: number;
  status: 'idle' | 'validating' | 'uploading' | 'processing' | 'complete' | 'error';
  error: string | null;
  reportId: string | null;
}

export default function UploadPage() {
  const navigate = useNavigate();
  const [dragActive, setDragActive] = useState(false);
  const [upload, setUpload] = useState<UploadState>({
    file: null,
    progress: 0,
    status: 'idle',
    error: null,
    reportId: null,
  });

  const validateFile = (file: File): string | null => {
    if (!ALLOWED_TYPES.includes(file.type)) {
      return `Invalid file type. Allowed: PDF, PNG, JPEG, DOCX`;
    }
    if (file.size > MAX_SIZE_MB * 1024 * 1024) {
      return `File too large. Maximum size: ${MAX_SIZE_MB}MB`;
    }
    return null;
  };

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  }, []);

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  };

  const handleFile = async (file: File) => {
    setUpload({ file, progress: 0, status: 'validating', error: null, reportId: null });
    
    const validationError = validateFile(file);
    if (validationError) {
      setUpload(prev => ({ ...prev, status: 'error', error: validationError }));
      return;
    }

    setUpload(prev => ({ ...prev, status: 'uploading', progress: 10 }));

    try {
      const progressInterval = setInterval(() => {
        setUpload(prev => ({
          ...prev,
          progress: Math.min(prev.progress + 10, 90),
        }));
      }, 200);

      const result = await api.uploadReport(file);

      clearInterval(progressInterval);
      setUpload(prev => ({
        ...prev,
        status: 'processing',
        progress: 100,
        reportId: result.id,
      }));

      setTimeout(() => {
        setUpload(prev => ({ ...prev, status: 'complete' }));
      }, 500);

    } catch (error: any) {
      const errorMessage = error?.response?.data?.detail || error?.message || 'Upload failed';
      
      if (errorMessage.includes('duplicate') || errorMessage.includes('already exists')) {
        setUpload(prev => ({
          ...prev,
          status: 'error',
          error: 'This file has already been uploaded. Check your report library.',
        }));
      } else {
        setUpload(prev => ({
          ...prev,
          status: 'error',
          error: errorMessage,
        }));
      }
    }
  };

  const resetUpload = () => {
    setUpload({
      file: null,
      progress: 0,
      status: 'idle',
      error: null,
      reportId: null,
    });
  };

  const getFileIcon = (file: File) => {
    if (file.type.startsWith('image/')) {
      return <ImageIcon className="text-purple-600" size={24} />;
    }
    return <FileText className="text-blue-600" size={24} />;
  };

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Upload Medical Report</h1>
        <p className="text-gray-600 mt-1">
          Upload your lab reports for analysis. Supported formats: PDF, PNG, JPEG, DOCX
        </p>
      </div>

      {upload.status === 'idle' && (
        <div
          className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
            dragActive
              ? 'border-blue-500 bg-blue-50'
              : 'border-gray-300 hover:border-gray-400'
          }`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <Upload className="mx-auto text-gray-400 mb-4" size={48} />
          <p className="text-lg font-medium text-gray-700 mb-2">
            Drag and drop your file here
          </p>
          <p className="text-gray-500 mb-4">or</p>
          <label className="inline-block">
            <input
              type="file"
              className="hidden"
              accept=".pdf,.png,.jpg,.jpeg,.docx"
              onChange={handleFileInput}
            />
            <span className="bg-blue-600 text-white px-6 py-2 rounded-lg cursor-pointer hover:bg-blue-700 transition-colors">
              Browse Files
            </span>
          </label>
          <p className="text-sm text-gray-500 mt-4">
            Maximum file size: {MAX_SIZE_MB}MB
          </p>
        </div>
      )}

      {upload.status !== 'idle' && upload.file && (
        <div className="bg-white border rounded-lg p-6">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center flex-shrink-0">
              {getFileIcon(upload.file)}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between">
                <p className="font-medium text-gray-900 truncate">
                  {upload.file.name}
                </p>
                {upload.status !== 'uploading' && upload.status !== 'processing' && (
                  <button
                    onClick={resetUpload}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <X size={20} />
                  </button>
                )}
              </div>
              <p className="text-sm text-gray-500">
                {(upload.file.size / 1024 / 1024).toFixed(2)} MB
              </p>

              {(upload.status === 'uploading' || upload.status === 'processing') && (
                <div className="mt-3">
                  <div className="flex items-center justify-between text-sm mb-1">
                    <span className="text-gray-600">
                      {upload.status === 'uploading' ? 'Uploading...' : 'Processing...'}
                    </span>
                    <span className="text-gray-600">{upload.progress}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${upload.progress}%` }}
                    />
                  </div>
                </div>
              )}

              {upload.status === 'complete' && (
                <div className="mt-3 flex items-center gap-2 text-green-600">
                  <CheckCircle size={18} />
                  <span className="text-sm font-medium">Upload complete!</span>
                </div>
              )}

              {upload.status === 'error' && (
                <div className="mt-3 flex items-center gap-2 text-red-600">
                  <AlertCircle size={18} />
                  <span className="text-sm">{upload.error}</span>
                </div>
              )}
            </div>
          </div>

          {upload.status === 'complete' && upload.reportId && (
            <div className="mt-6 flex gap-3">
              <button
                onClick={() => navigate(`/reports/${upload.reportId}`)}
                className="flex-1 bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 transition-colors"
              >
                View Report
              </button>
              <button
                onClick={resetUpload}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Upload Another
              </button>
            </div>
          )}

          {upload.status === 'error' && (
            <div className="mt-6">
              <button
                onClick={resetUpload}
                className="w-full bg-gray-100 text-gray-700 py-2 rounded-lg hover:bg-gray-200 transition-colors"
              >
                Try Again
              </button>
            </div>
          )}
        </div>
      )}

      <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="font-semibold text-blue-900 mb-2">Tips for best results:</h3>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>• Ensure the document is clear and readable</li>
          <li>• For scanned documents, use high resolution (300 DPI)</li>
          <li>• Make sure all text is visible and not cut off</li>
          <li>• PDF files work best for digital lab reports</li>
        </ul>
      </div>
    </div>
  );
}
