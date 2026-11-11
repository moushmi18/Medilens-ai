import { Shield } from 'lucide-react';
import { ComingSoon } from '../components';

export default function PrivacyCenterPage() {
  return (
    <ComingSoon
      title="Privacy Center"
      description="Control your data with transparency. View, export, or delete your health information at any time."
      phase={10}
      icon={<Shield size={32} />}
      features={[
        'View all stored data associated with your account',
        'Delete individual reports and their AI analysis',
        'Delete conversation history',
        'Set data retention preferences',
        'Export your data in standard formats',
        'View audit log of data access (no medical content)',
        'Clear explanation of encryption practices',
      ]}
    />
  );
}
