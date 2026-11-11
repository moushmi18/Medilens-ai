import { FileHeart } from 'lucide-react';
import { ComingSoon } from '../components';

export default function DoctorSummaryPage() {
  return (
    <ComingSoon
      title="Doctor Discussion Summary"
      description="Generate a PDF summary of your report to facilitate informed discussions with your healthcare provider."
      phase={10}
      icon={<FileHeart size={32} />}
      features={[
        'Comprehensive summary of report findings',
        'Values outside reference ranges highlighted',
        'Plain-language explanations for each result',
        'Suggested questions to ask your doctor',
        'References to trusted medical sources',
        'Downloadable PDF format',
        'Never includes diagnosis or treatment advice',
      ]}
    />
  );
}
