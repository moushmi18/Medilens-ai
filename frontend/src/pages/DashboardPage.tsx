import { LayoutDashboard } from 'lucide-react';
import { ComingSoon } from '../components';

export default function DashboardPage() {
  return (
    <ComingSoon
      title="Dashboard"
      description="Your personalized health information hub with report statistics, recent activity, and quick access to key features."
      phase={2}
      icon={<LayoutDashboard size={32} />}
      features={[
        'Total reports uploaded, processed, and processing counts',
        'Recent reports with status indicators',
        'Recent AI conversations',
        'Quick upload and chat entry points',
        'Processing status notifications',
      ]}
    />
  );
}
