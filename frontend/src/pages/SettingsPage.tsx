import { Settings } from 'lucide-react';
import { ComingSoon } from '../components';

export default function SettingsPage() {
  return (
    <ComingSoon
      title="Settings"
      description="Customize your MediLens AI experience with personal preferences and account settings."
      phase={2}
      icon={<Settings size={32} />}
      features={[
        'Update profile information',
        'Change password',
        'Email notification preferences',
        'Language and region settings',
        'Theme preferences (light/dark)',
        'Default report view settings',
      ]}
    />
  );
}
