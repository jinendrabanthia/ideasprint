import { useState, useEffect } from 'react';
import { useAuth } from '../AuthContext';
import { useNavigate } from 'react-router-dom';
import logoImg from '../assets/logo.png';

export default function AuthPage() {
  const [mode, setMode] = useState<'signin' | 'signup'>('signin');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [role, setRole] = useState<'senior' | 'caregiver'>('senior');
  const [loading, setLoading] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);
  const [error, setError] = useState('');
  const [showGoogleModal, setShowGoogleModal] = useState(false);
  const [customGoogleEmail, setCustomGoogleEmail] = useState('');
  const [customGoogleName, setCustomGoogleName] = useState('');
  const [showCustomGoogleInput, setShowCustomGoogleInput] = useState(false);

  const { signIn, signUp, signInWithGoogle } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    // If Google Client ID is configured, initialize Google Identity Services
    const clientId = (import.meta as any).env?.VITE_GOOGLE_CLIENT_ID;
    if (clientId && (window as any).google?.accounts?.id) {
      try {
        (window as any).google.accounts.id.initialize({
          client_id: clientId,
          callback: handleGoogleCredentialResponse,
        });
      } catch (e) {
        console.warn('Google GSI init notice:', e);
      }
    }
  }, [role]);

  const handleGoogleCredentialResponse = async (response: any) => {
    setGoogleLoading(true);
    setError('');
    try {
      await signInWithGoogle({
        id_token: response.credential,
        role,
      });
      navigate(role === 'senior' ? '/' : '/caregiver');
    } catch (err: any) {
      setError(err.message || 'Google Sign-In failed. Please try again.');
    } finally {
      setGoogleLoading(false);
    }
  };

  const handleSelectGoogleAccount = async (accountEmail: string, accountName: string) => {
    setGoogleLoading(true);
    setError('');
    setShowGoogleModal(false);

    try {
      await signInWithGoogle({
        email: accountEmail,
        display_name: accountName,
        google_id: `g_${accountEmail.replace(/[^a-zA-Z0-9]/g, '')}`,
        role,
      });
      navigate(role === 'senior' ? '/' : '/caregiver');
    } catch (err: any) {
      setError(err.message || 'Google Sign-In failed. Please try again.');
    } finally {
      setGoogleLoading(false);
    }
  };

  const handleCustomGoogleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!customGoogleEmail) return;
    const fallbackName = customGoogleName.trim() || customGoogleEmail.split('@')[0];
    handleSelectGoogleAccount(customGoogleEmail.trim().toLowerCase(), fallbackName);
  };

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
          <div className="auth-card__logo" style={{ textAlign: 'center', marginBottom: '14px' }}>
            <img
              src={logoImg}
              alt="Sahara Logo"
              style={{
                width: '88px',
                height: '88px',
                borderRadius: '24px',
                boxShadow: '0 10px 25px rgba(217, 107, 67, 0.25)',
                display: 'inline-block',
                objectFit: 'cover',
              }}
            />
          </div>
          <h1 className="auth-card__title">Sahara</h1>
          <p className="auth-card__subtitle">Your caring daily companion</p>
        </div>

        <div className="disclaimer" style={{ marginBottom: '1.25rem', fontSize: 'var(--text-xs)' }}>
          ℹ️ Sahara is a care companion, not a medical device or emergency service. 
          It helps with reminders and daily check-ins but cannot diagnose conditions or replace professional care.
        </div>

        {/* Role Selector */}
        <div style={{ marginBottom: '1.25rem' }}>
          <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '6px' }}>
            I am signing in as:
          </label>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              type="button"
              className={`btn-toggle ${role === 'senior' ? 'active' : ''}`}
              onClick={() => setRole('senior')}
              style={{
                flex: 1,
                padding: '12px 14px',
                fontSize: '15px',
                fontWeight: 600,
                borderRadius: '12px',
                border: role === 'senior' ? '2px solid var(--terracotta)' : '2px solid var(--border)',
                background: role === 'senior' ? 'var(--terracotta-light, #FFF3ED)' : '#FFFFFF',
                color: role === 'senior' ? 'var(--terracotta, #D96B43)' : 'var(--text-primary)',
                cursor: 'pointer',
              }}
            >
              👵 Senior Companion
            </button>
            <button
              type="button"
              className={`btn-toggle ${role === 'caregiver' ? 'active' : ''}`}
              onClick={() => setRole('caregiver')}
              style={{
                flex: 1,
                padding: '12px 14px',
                fontSize: '15px',
                fontWeight: 600,
                borderRadius: '12px',
                border: role === 'caregiver' ? '2px solid var(--sage, #4A7C59)' : '2px solid var(--border)',
                background: role === 'caregiver' ? 'var(--sage-light, #EDF5F0)' : '#FFFFFF',
                color: role === 'caregiver' ? 'var(--sage, #4A7C59)' : 'var(--text-primary)',
                cursor: 'pointer',
              }}
            >
              🤝 Family / Caregiver
            </button>
          </div>
        </div>

        {/* Primary Google Sign-In Button */}
        <div style={{ marginBottom: '1.25rem' }}>
          <button
            type="button"
            className="btn-google-auth"
            onClick={() => setShowGoogleModal(true)}
            disabled={googleLoading}
            style={{
              width: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '12px',
              backgroundColor: '#FFFFFF',
              color: '#3c4043',
              border: '2px solid #dadce0',
              borderRadius: '9999px',
              padding: '14px 18px',
              fontSize: '16px',
              fontWeight: 600,
              cursor: 'pointer',
              minHeight: '52px',
              boxShadow: '0 2px 5px rgba(0,0,0,0.08)',
              transition: 'all 0.2s ease',
            }}
          >
            <svg width="22" height="22" viewBox="0 0 24 24">
              <path
                fill="#4285F4"
                d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
              />
              <path
                fill="#34A853"
                d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
              />
              <path
                fill="#FBBC05"
                d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
              />
              <path
                fill="#EA4335"
                d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
              />
            </svg>
            <span>{googleLoading ? 'Connecting to Google...' : `Sign in with Google as ${role === 'senior' ? 'Senior' : 'Caregiver'}`}</span>
          </button>
        </div>

        {/* Divider */}
        <div style={{ display: 'flex', alignItems: 'center', margin: '1.25rem 0', color: 'var(--text-muted)', fontSize: '13px' }}>
          <div style={{ flex: 1, height: '1px', backgroundColor: 'var(--border)' }} />
          <span style={{ padding: '0 12px' }}>or sign in with password</span>
          <div style={{ flex: 1, height: '1px', backgroundColor: 'var(--border)' }} />
        </div>

        {/* Auth Tabs */}
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
          <div className="alert alert--error animate-fade-in" role="alert" style={{ margin: '1rem 0' }}>
            <span>⚠️</span>
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          {mode === 'signup' && (
            <div className="form-group animate-fade-in-up">
              <label className="form-label" htmlFor="displayName">Your Full Name</label>
              <input
                id="displayName"
                type="text"
                className="form-input"
                placeholder="e.g. Eleanor Vance"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                required
                autoComplete="name"
              />
            </div>
          )}

          <div className="form-group">
            <label className="form-label" htmlFor="email">Email Address</label>
            <input
              id="email"
              type="email"
              className="form-input"
              placeholder="name@example.com"
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
              placeholder="Minimum 6 characters"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={6}
              autoComplete={mode === 'signin' ? 'current-password' : 'new-password'}
            />
          </div>

          <button
            type="submit"
            className="btn btn--primary btn--large"
            style={{ width: '100%', marginTop: 'var(--space-md)' }}
            disabled={loading}
          >
            {loading ? (
              <span className="spinner" style={{ width: 24, height: 24, borderWidth: 3 }} />
            ) : mode === 'signin' ? (
              'Sign In with Email'
            ) : (
              'Create Account with Email'
            )}
          </button>
        </form>
      </div>

      {/* Google Account Chooser Modal (Realistic Google Single Sign-On Dialog) */}
      {showGoogleModal && (
        <div
          className="modal-backdrop"
          onClick={() => setShowGoogleModal(false)}
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(0,0,0,0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            padding: '1rem',
          }}
        >
          <div
            className="modal-content"
            onClick={(e) => e.stopPropagation()}
            style={{
              backgroundColor: '#FFFFFF',
              borderRadius: '24px',
              maxWidth: '460px',
              width: '100%',
              padding: '28px',
              boxShadow: '0 20px 40px rgba(0,0,0,0.2)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <svg width="24" height="24" viewBox="0 0 24 24">
                  <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                  <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                  <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z" />
                  <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z" />
                </svg>
                <h3 style={{ margin: 0, fontSize: '18px', fontWeight: 600 }}>Sign in with Google</h3>
              </div>
              <button
                type="button"
                onClick={() => setShowGoogleModal(false)}
                style={{ background: 'none', border: 'none', fontSize: '22px', cursor: 'pointer', color: 'var(--text-muted)' }}
              >
                ✕
              </button>
            </div>

            <p style={{ fontSize: '14px', color: 'var(--text-secondary)', marginBottom: '20px' }}>
              Choose a Google account to continue to <strong>Sahara Elder Companion</strong>:
            </p>

            {/* Quick 1-Tap Google Accounts */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginBottom: '20px' }}>
              <button
                type="button"
                onClick={() => handleSelectGoogleAccount('eleanor.vance@gmail.com', 'Eleanor Vance')}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '14px',
                  padding: '12px 16px',
                  borderRadius: '14px',
                  border: '1px solid var(--border)',
                  background: '#FFFFFF',
                  cursor: 'pointer',
                  textAlign: 'left',
                  transition: 'background-color 0.2s',
                }}
                onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = '#F8F9FA')}
                onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = '#FFFFFF')}
              >
                <div style={{ width: '40px', height: '40px', borderRadius: '50%', background: '#D96B43', color: '#FFF', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold' }}>
                  EV
                </div>
                <div>
                  <div style={{ fontWeight: 600, fontSize: '15px' }}>Eleanor Vance</div>
                  <div style={{ fontSize: '13px', color: 'var(--text-muted)' }}>eleanor.vance@gmail.com (Senior)</div>
                </div>
              </button>

              <button
                type="button"
                onClick={() => handleSelectGoogleAccount('sarah.jenkins@gmail.com', 'Sarah Jenkins')}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '14px',
                  padding: '12px 16px',
                  borderRadius: '14px',
                  border: '1px solid var(--border)',
                  background: '#FFFFFF',
                  cursor: 'pointer',
                  textAlign: 'left',
                  transition: 'background-color 0.2s',
                }}
                onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = '#F8F9FA')}
                onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = '#FFFFFF')}
              >
                <div style={{ width: '40px', height: '40px', borderRadius: '50%', background: '#4A7C59', color: '#FFF', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold' }}>
                  SJ
                </div>
                <div>
                  <div style={{ fontWeight: 600, fontSize: '15px' }}>Sarah Jenkins</div>
                  <div style={{ fontSize: '13px', color: 'var(--text-muted)' }}>sarah.jenkins@gmail.com (Caregiver)</div>
                </div>
              </button>
            </div>

            {/* Custom Google Account Option */}
            {!showCustomGoogleInput ? (
              <button
                type="button"
                onClick={() => setShowCustomGoogleInput(true)}
                style={{
                  width: '100%',
                  padding: '12px',
                  background: 'none',
                  border: '1px dashed var(--border)',
                  borderRadius: '12px',
                  color: 'var(--text-primary)',
                  fontWeight: 600,
                  fontSize: '14px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                }}
              >
                <span>➕</span> Use another Google account
              </button>
            ) : (
              <form onSubmit={handleCustomGoogleSubmit} style={{ marginTop: '12px' }}>
                <input
                  type="email"
                  required
                  placeholder="Enter your Gmail address (e.g. john@gmail.com)"
                  value={customGoogleEmail}
                  onChange={(e) => setCustomGoogleEmail(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '12px 14px',
                    borderRadius: '10px',
                    border: '1px solid var(--border)',
                    marginBottom: '8px',
                    fontSize: '14px',
                  }}
                />
                <input
                  type="text"
                  placeholder="Your Name (optional)"
                  value={customGoogleName}
                  onChange={(e) => setCustomGoogleName(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '12px 14px',
                    borderRadius: '10px',
                    border: '1px solid var(--border)',
                    marginBottom: '12px',
                    fontSize: '14px',
                  }}
                />
                <div style={{ display: 'flex', gap: '8px' }}>
                  <button
                    type="button"
                    onClick={() => setShowCustomGoogleInput(false)}
                    style={{ flex: 1, padding: '10px', borderRadius: '10px', border: '1px solid var(--border)', background: '#FFF', cursor: 'pointer' }}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    style={{ flex: 2, padding: '10px', borderRadius: '10px', border: 'none', background: 'var(--terracotta, #D96B43)', color: '#FFF', fontWeight: 600, cursor: 'pointer' }}
                  >
                    Continue with this Google Account
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
