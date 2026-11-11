import { Routes, Route } from 'react-router-dom';
import { MainLayout, AuthLayout } from './layouts';
import {
  LoginPage,
  RegisterPage,
  DashboardPage,
  UploadPage,
  ReportLibraryPage,
  ReportViewerPage,
  ChatPage,
  ComparePage,
  DoctorSummaryPage,
  PrivacyCenterPage,
  SettingsPage,
} from './pages';

export default function App() {
  return (
    <Routes>
      {/* Auth routes */}
      <Route element={<AuthLayout />}>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
      </Route>

      {/* Main app routes */}
      <Route element={<MainLayout />}>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/upload" element={<UploadPage />} />
        <Route path="/reports" element={<ReportLibraryPage />} />
        <Route path="/reports/:id" element={<ReportViewerPage />} />
        <Route path="/chat" element={<ChatPage />} />
        <Route path="/compare" element={<ComparePage />} />
        <Route path="/summary" element={<DoctorSummaryPage />} />
        <Route path="/privacy" element={<PrivacyCenterPage />} />
        <Route path="/settings" element={<SettingsPage />} />
      </Route>
    </Routes>
  );
}
