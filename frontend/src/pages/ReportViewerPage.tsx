import { FileSearch } from 'lucide-react';
import { ComingSoon } from '../components';

export default function ReportViewerPage() {
  return (
    <ComingSoon
      title="Report Viewer"
      description="View your medical report alongside AI-extracted data with explanations for each result."
      phase={4}
      icon={<FileSearch size={32} />}
      features={[
        'Split-screen view: original document on left, extracted data on right',
        'Extracted lab values with reference ranges',
        'Click any value to see plain-language explanation',
        'Highlight abnormal or out-of-range values',
        'Flag uncertain OCR extractions for verification',
        'Links to trusted medical information sources',
      ]}
    />
  );
}
