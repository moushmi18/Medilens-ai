import { GitCompare } from 'lucide-react';
import { ComingSoon } from '../components';

export default function ComparePage() {
  return (
    <ComingSoon
      title="Compare Reports"
      description="Compare lab results between two reports to track changes over time with clear visualizations."
      phase={10}
      icon={<GitCompare size={32} />}
      features={[
        'Select two reports for side-by-side comparison',
        'Automatic matching of common tests',
        'Visual charts showing value changes',
        'Display each report\'s own reference ranges',
        'Never assumes direction of change is good/bad',
        'Highlights incompatible units or unrelated tests',
        'Export comparison as PDF',
      ]}
    />
  );
}
