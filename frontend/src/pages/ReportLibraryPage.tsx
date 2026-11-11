import { FileText } from 'lucide-react';
import { ComingSoon } from '../components';

export default function ReportLibraryPage() {
  return (
    <ComingSoon
      title="Report Library"
      description="Browse and manage all your uploaded medical reports in one secure location."
      phase={3}
      icon={<FileText size={32} />}
      features={[
        'List all uploaded reports with status',
        'Search and filter by date, type, or status',
        'Quick view of report metadata',
        'One-click access to detailed report view',
        'Delete reports with confirmation',
        'Download original files',
      ]}
    />
  );
}
