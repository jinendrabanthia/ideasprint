import { useState } from 'react';
import { useAuth } from '../AuthContext';
import { useNavigate } from 'react-router-dom';

export default function AuthPage() {
  const [mode, setMode] = useState<'signin' | 'signup'>('signin');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [role, setRole] = useState('senior');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const { signIn, signUp } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      if (mode === 'signin') {
        await signIn(email, password);
        navigate('/');
      } else {
        await signUp(email, password, displayName, role);
        navigate('/onboarding');
      }
    } catch (err: any) {
      setError(err.message || 'Something went wrong. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-card__header">
          <div className="auth-card__logo">🌻</div>
          <h1 className="auth-card__title">Sahara</h1>
          <p className="auth-card__subtitle">Your caring daily companion</p>
        </div>

        <div className="disclaimer" style={{ marginBottom: '1.5rem', fontSize: 'var(--text-xs)' }}>
          ℹ️ Sahara is a care companion, not a medical device or emergency service. 
          It helps with reminders and daily check-ins but cannot diagnose conditions or replace professional care.
        </div>

        <div className="auth-tabs">
          <button
            className={`auth-tab ${mode === 'signin' ? 'auth-tab--active' : ''}`}
            onClick={() => { setMode('signin'); setError(''); }}
          >
            Sign In
          </button>
          <button
            className={`auth-tab ${mode === 'signup' ? 'auth-tab--active' : ''}`}
            onClick={() => { setMode('signup'); setError(''); }}
          >
            Create Account
          </button>
        </div>

        {error && (
          <div className="alert alert--error animate-fade-in" role="alert">
            <span>⚠️</span>
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          {mode === 'signup' && (
            <div className="form-group animate-fade-in-up">
              <label className="form-label" htmlFor="displayName">Your Name</label>
              <input
                id="displayName"
                type="text"
                className="form-input"
                placeholder="How should we call you?"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                required
                autoComplete="name"
              />
            </div>
          )}

          <div className="form-group">
            <label className="form-label" htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              className="form-input"
              placeholder="your.email@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              className="form-input"
              placeholder="Choose a secure password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={6}
              autoComplete={mode === 'signin' ? 'current-password' : 'new-password'}
            />
          </div>

          {mode === 'signup' && (
            <div className="form-group animate-fade-in-up">
              <label className="form-label" htmlFor="role">I am a</label>
              <select
                id="role"
                className="form-input"
                value={role}
                onChange={(e) => setRole(e.target.value)}
              >
                <option value="senior">Senior (using the companion)</option>
                <option value="caregiver">Caregiver (helping a senior)</option>
              </select>
            </div>
          )}

          <button
            type="submit"
            className="btn btn--primary btn--large"
            style={{ width: '100%', marginTop: 'var(--space-md)' }}
            disabled={loading}
          >
            {loading ? (
              <span className="spinner" style={{ width: 24, height: 24, borderWidth: 3 }} />
            ) : mode === 'signin' ? (
              'Sign In'
            ) : (
              'Create Account'
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
