import { createContext, useContext, useState, useEffect, type ReactNode } from 'react';
import api from './api';

interface User {
  id: string;
  email: string;
  role: string;
  profileId: string | null;
  displayName: string;
  token: string;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  error: string;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string, displayName: string, role?: string) => Promise<void>;
  signInWithGoogle: (googleData: {
    id_token?: string;
    email?: string;
    display_name?: string;
    google_id?: string;
    role?: string;
  }) => Promise<void>;
  signOut: () => void;
  clearError: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    // Restore session from localStorage
    const saved = localStorage.getItem('afe_session');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        api.setToken(parsed.token);
        setUser(parsed);
      } catch {}
    }
    setLoading(false);
  }, []);

  const signIn = async (email: string, password: string) => {
    setError('');
    setLoading(true);
    try {
      const res = await api.signIn(email, password);
      const userData: User = {
        id: res.user_id,
        email: res.email,
        role: res.role,
        profileId: res.profile_id,
        displayName: res.display_name,
        token: res.access_token,
      };
      api.setToken(res.access_token);
      setUser(userData);
      localStorage.setItem('afe_session', JSON.stringify(userData));
    } catch (e: any) {
      setError(e.message || 'Sign in failed');
      throw e;
    } finally {
      setLoading(false);
    }
  };

  const signUp = async (email: string, password: string, displayName: string, role = 'senior') => {
    setError('');
    setLoading(true);
    try {
      const res = await api.signUp(email, password, displayName, role);
      const userData: User = {
        id: res.user_id,
        email: res.email,
        role: res.role,
        profileId: res.profile_id,
        displayName: res.display_name,
        token: res.access_token,
      };
      api.setToken(res.access_token);
      setUser(userData);
      localStorage.setItem('afe_session', JSON.stringify(userData));
    } catch (e: any) {
      setError(e.message || 'Sign up failed');
      throw e;
    } finally {
      setLoading(false);
    }
  };

  const signInWithGoogle = async (googleData: {
    id_token?: string;
    email?: string;
    display_name?: string;
    google_id?: string;
    role?: string;
  }) => {
    setError('');
    setLoading(true);
    try {
      const res = await api.signInWithGoogle(googleData);
      const userData: User = {
        id: res.user_id,
        email: res.email,
        role: res.role,
        profileId: res.profile_id,
        displayName: res.display_name,
        token: res.access_token,
      };
      api.setToken(res.access_token);
      setUser(userData);
      localStorage.setItem('afe_session', JSON.stringify(userData));
    } catch (e: any) {
      setError(e.message || 'Google Sign-In failed');
      throw e;
    } finally {
      setLoading(false);
    }
  };

  const signOut = () => {
    api.setToken(null);
    setUser(null);
    localStorage.removeItem('afe_session');
  };

  const clearError = () => setError('');

  return (
    <AuthContext.Provider value={{ user, loading, error, signIn, signUp, signInWithGoogle, signOut, clearError }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
