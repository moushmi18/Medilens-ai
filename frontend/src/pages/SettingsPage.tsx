import { useState, useEffect } from 'react';
import { 
  User, 
  Bell, 
  Shield, 
  Palette,
  Save,
  CheckCircle,
  Loader2,
} from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { api } from '../services/api';

type PrefKey =
  | 'email_notifications'
  | 'processing_alerts'
  | 'dark_mode'
  | 'show_confidence'
  | 'auto_process';

interface Preferences {
  email_notifications: boolean;
  processing_alerts: boolean;
  dark_mode: boolean;
  show_confidence: boolean;
  auto_process: boolean;
}

const DEFAULT_PREFS: Preferences = {
  email_notifications: true,
  processing_alerts: true,
  dark_mode: false,
  show_confidence: true,
  auto_process: false,
};

export default function SettingsPage() {
  const { user } = useAuth();
  const [saved, setSaved] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [settings, setSettings] = useState<Preferences>(DEFAULT_PREFS);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const data = await api.getSettings();
        if (!cancelled) {
          setSettings({ ...DEFAULT_PREFS, ...data.preferences });
        }
      } catch (err: any) {
        if (!cancelled) {
          setError(err?.message || 'Failed to load settings');
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    try {
      const data = await api.updateSettings(settings);
      setSettings({ ...DEFAULT_PREFS, ...data.preferences });
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch (err: any) {
      setError(err?.message || 'Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  const handleChange = (key: PrefKey) => {
    setSettings(prev => ({ ...prev, [key]: !prev[key] }));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="animate-spin text-blue-600" size={32} />
      </div>
    );
  }

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-600">Manage your account and application preferences</p>
      </div>

      {error && (
        <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
          {error}
        </div>
      )}

      <div className="space-y-6">
        <div className="bg-white rounded-lg border p-6">
          <div className="flex items-center gap-3 mb-4">
            <User className="text-blue-600" size={20} />
            <h2 className="font-semibold text-gray-900">Account</h2>
          </div>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
              <input
                type="text"
                value={user?.fullName || ''}
                disabled
                className="w-full px-3 py-2 border rounded-lg bg-gray-50 text-gray-500"
              />
            </div>
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
                checked={settings.email_notifications}
                onChange={() => handleChange('email_notifications')}
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
                checked={settings.processing_alerts}
                onChange={() => handleChange('processing_alerts')}
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
                checked={settings.show_confidence}
                onChange={() => handleChange('show_confidence')}
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
                checked={settings.dark_mode}
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
                checked={settings.auto_process}
                onChange={() => handleChange('auto_process')}
                className="w-5 h-5 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
            </label>
          </div>
        </div>

        <button
          onClick={handleSave}
          disabled={saving}
          className="w-full bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
        >
          {saving ? (
            <>
              <Loader2 size={20} className="animate-spin" />
              Saving…
            </>
          ) : saved ? (
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
