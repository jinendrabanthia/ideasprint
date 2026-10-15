import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './AuthContext';
import AuthPage from './pages/AuthPage';
import Onboarding from './pages/Onboarding';
import Home from './pages/Home';
import Chat from './pages/Chat';
import Reminders from './pages/Reminders';
import CheckIn from './pages/CheckIn';
import Settings from './pages/Settings';
import CaregiverDashboard from './pages/CaregiverDashboard';
import Layout from './components/Layout';
import './index.css';

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) {
    return (
      <div className="loading-screen">
        <div className="spinner" />
        <p>Loading...</p>
      </div>
    );
  }
  if (!user) return <Navigate to="/auth" replace />;
  return <>{children}</>;
}

function AppRoutes() {
  const { user } = useAuth();

  return (
    <Routes>
      <Route path="/auth" element={user ? <Navigate to="/" replace /> : <AuthPage />} />
      <Route
        path="/onboarding"
        element={
          <ProtectedRoute>
            <Onboarding />
          </ProtectedRoute>
        }
      />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Home />} />
        <Route path="chat" element={<Chat />} />
        <Route path="reminders" element={<Reminders />} />
        <Route path="checkin" element={<CheckIn />} />
        <Route path="settings" element={<Settings />} />
        <Route path="caregiver" element={<CaregiverDashboard />} />
      </Route>
    </Routes>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
}
