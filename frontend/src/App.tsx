import { lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './AuthContext';
import './index.css';

const AuthPage = lazy(() => import('./pages/AuthPage'));
const Onboarding = lazy(() => import('./pages/Onboarding'));
const Home = lazy(() => import('./pages/Home'));
const Chat = lazy(() => import('./pages/Chat'));
const Reminders = lazy(() => import('./pages/Reminders'));
const CheckIn = lazy(() => import('./pages/CheckIn'));
const Settings = lazy(() => import('./pages/Settings'));
const CaregiverDashboard = lazy(() => import('./pages/CaregiverDashboard'));
const Layout = lazy(() => import('./components/Layout'));

function LoadingFallback() {
  return (
    <div className="loading-screen" aria-live="polite" role="status">
      <div className="spinner" />
      <p>Loading Sahara...</p>
    </div>
  );
}

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) {
    return <LoadingFallback />;
  }
  if (!user) return <Navigate to="/auth" replace />;
  return <>{children}</>;
}

function AppRoutes() {
  const { user } = useAuth();

  return (
    <Suspense fallback={<LoadingFallback />}>
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
    </Suspense>
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
