import { Upload } from 'lucide-react';
import { ComingSoon } from '../components';

export default function UploadPage() {
  return (
    <ComingSoon
      title="Upload Report"
      description="Securely upload your medical reports for AI-powered analysis and explanations."
      phase={3}
      icon={<Upload size={32} />}
      features={[
        'Support for PDF, scanned PDF, JPG, PNG, and DOCX files',
        'Drag-and-drop interface with upload progress',
        'File validation and size limit checks',
        'Duplicate detection to avoid redundant processing',
        'Processing status tracking',
        'Preview before and after upload',
      ]}
    />
  );
}
