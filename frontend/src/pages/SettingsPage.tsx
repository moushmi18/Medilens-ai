import { useState } from 'react';
import { 
  User, 
  Bell, 
  Shield, 
  Palette,
  Save,
  CheckCircle,
} from 'lucide-react';
import { useAuth } from '../hooks/useAuth';

export default function SettingsPage() {
  const { user } = useAuth();
  const [saved, setSaved] = useState(false);
  const [settings, setSettings] = useState({
    emailNotifications: true,
    processingAlerts: true,
    darkMode: false,
    showConfidence: true,
    autoProcess: false,
  });

  const handleSave = () => {
    localStorage.setItem('medilens_settings', JSON.stringify(settings));
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const handleChange = (key: keyof typeof settings) => {
    setSettings(prev => ({ ...prev, [key]: !prev[key] }));
  };

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-600">Manage your account and application preferences</p>
      </div>

      <div className="space-y-6">
        <div className="bg-white rounded-lg border p-6">
          <div className="flex items-center gap-3 mb-4">
            <User className="text-blue-600" size={20} />
            <h2 className="font-semibold text-gray-900">Account</h2>
          </div>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <input
                type="email"
                value={user?.email || ''}
                disabled
                className="w-full px-3 py-2 border rounded-lg bg-gray-50 text-gray-500"
              />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg border p-6">
          <div className="flex items-center gap-3 mb-4">
            <Bell className="text-blue-600" size={20} />
            <h2 className="font-semibold text-gray-900">Notifications</h2>
          </div>
          <div className="space-y-4">
            <label className="flex items-center justify-between cursor-pointer">
              <div>
                <p className="font-medium text-gray-900">Email Notifications</p>
                <p className="text-sm text-gray-500">Receive updates about your reports</p>
              </div>
              <input
                type="checkbox"
                checked={settings.emailNotifications}
                onChange={() => handleChange('emailNotifications')}
                className="w-5 h-5 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
            </label>
            <label className="flex items-center justify-between cursor-pointer">
              <div>
                <p className="font-medium text-gray-900">Processing Alerts</p>
                <p className="text-sm text-gray-500">Get notified when reports are processed</p>
              </div>
              <input
                type="checkbox"
                checked={settings.processingAlerts}
                onChange={() => handleChange('processingAlerts')}
                className="w-5 h-5 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
            </label>
          </div>
        </div>

        <div className="bg-white rounded-lg border p-6">
          <div className="flex items-center gap-3 mb-4">
            <Palette className="text-blue-600" size={20} />
            <h2 className="font-semibold text-gray-900">Display</h2>
          </div>
          <div className="space-y-4">
            <label className="flex items-center justify-between cursor-pointer">
              <div>
                <p className="font-medium text-gray-900">Show Confidence Scores</p>
                <p className="text-sm text-gray-500">Display OCR confidence for extracted values</p>
              </div>
              <input
                type="checkbox"
                checked={settings.showConfidence}
                onChange={() => handleChange('showConfidence')}
                className="w-5 h-5 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
            </label>
            <label className="flex items-center justify-between cursor-pointer opacity-50">
              <div>
                <p className="font-medium text-gray-900">Dark Mode</p>
                <p className="text-sm text-gray-500">Use dark theme (coming soon)</p>
              </div>
              <input
                type="checkbox"
                checked={settings.darkMode}
                disabled
                className="w-5 h-5 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
            </label>
          </div>
        </div>

        <div className="bg-white rounded-lg border p-6">
          <div className="flex items-center gap-3 mb-4">
            <Shield className="text-blue-600" size={20} />
            <h2 className="font-semibold text-gray-900">Processing</h2>
          </div>
          <div className="space-y-4">
            <label className="flex items-center justify-between cursor-pointer">
              <div>
                <p className="font-medium text-gray-900">Auto-Process Reports</p>
                <p className="text-sm text-gray-500">Automatically extract data when uploading</p>
              </div>
              <input
                type="checkbox"
                checked={settings.autoProcess}
                onChange={() => handleChange('autoProcess')}
                className="w-5 h-5 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
            </label>
          </div>
        </div>

        <button
          onClick={handleSave}
          className="w-full bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 transition-colors flex items-center justify-center gap-2"
        >
          {saved ? (
            <>
              <CheckCircle size={20} />
              Settings Saved!
            </>
          ) : (
            <>
              <Save size={20} />
              Save Settings
            </>
          )}
        </button>
      </div>
    </div>
  );
}
