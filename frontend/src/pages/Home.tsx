import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../AuthContext';
import api from '../api';

export default function Home() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [reminders, setReminders] = useState<any[]>([]);
  const [nextReminder, setNextReminder] = useState<any>(null);
  const [checkin, setCheckin] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [voiceState, setVoiceState] = useState<'idle' | 'listening' | 'thinking' | 'speaking' | 'error'>('idle');
  const [statusMsg, setStatusMsg] = useState('');

  const timeOfDay = () => {
    const h = new Date().getHours();
    if (h < 12) return 'Good morning';
    if (h < 17) return 'Good afternoon';
    return 'Good evening';
  };

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    setLoading(true);
    try {
      const today = new Date().toISOString().split('T')[0];
      const [remindersRes, nextRes, checkinRes] = await Promise.allSettled([
        api.listReminders(today),
        api.getNextReminder(),
        api.getTodayCheckin(),
      ]);

      if (remindersRes.status === 'fulfilled') setReminders(remindersRes.value?.reminders || []);
      if (nextRes.status === 'fulfilled') setNextReminder(nextRes.value);
      if (checkinRes.status === 'fulfilled') setCheckin(checkinRes.value);
    } catch { }
    setLoading(false);
  };

  const handleTalk = () => {
    navigate('/chat');
  };

  const handleHelp = async () => {
    setVoiceState('thinking');
    setStatusMsg('Reaching out for help...');
    try {
      const res = await api.requestHelp('Help requested from home screen', 'medium');
      setStatusMsg(res.is_simulated
        ? '📱 [SIMULATED] Help notification sent to your trusted contacts.'
        : '📱 Help notification sent to your trusted contacts.');
      setVoiceState('idle');
      setTimeout(() => setStatusMsg(''), 5000);
    } catch (err: any) {
      setStatusMsg('Could not send help request. Please call your emergency number.');
      setVoiceState('error');
      setTimeout(() => { setStatusMsg(''); setVoiceState('idle'); }, 5000);
    }
  };

  return (
    <div className="animate-fade-in">
      {/* Greeting */}
      <div className="home-greeting">
        <p className="home-greeting__time">{timeOfDay()}</p>
        <h1 className="home-greeting__name">{user?.displayName || 'Friend'} 👋</h1>
      </div>

      {/* Status Message */}
      {statusMsg && (
        <div className={`alert ${voiceState === 'error' ? 'alert--error' : 'alert--info'} animate-fade-in-up`}>
          {statusMsg}
        </div>
      )}

      {/* Talk Button */}
      <div className="talk-section animate-fade-in-up stagger-1">
        <p className="talk-section__label">Tap to talk with Sahara</p>
        <button
          className={`btn btn--talk ${voiceState === 'listening' ? 'listening' : ''}`}
          onClick={handleTalk}
          aria-label="Start conversation"
        >
          🎤
        </button>
        {voiceState !== 'idle' && (
          <div className={`voice-indicator voice-indicator--${voiceState}`}>
            {voiceState === 'listening' && (
              <>
                <div className="voice-bar" />
                <div className="voice-bar" />
                <div className="voice-bar" />
                <div className="voice-bar" />
                <span style={{ marginLeft: 8 }}>Listening...</span>
              </>
            )}
            {voiceState === 'thinking' && <span>Thinking...</span>}
            {voiceState === 'speaking' && <span>Speaking...</span>}
            {voiceState === 'error' && <span>Something went wrong</span>}
          </div>
        )}
      </div>

      {/* Dashboard Grid */}
      <div className="home-grid animate-fade-in-up stagger-2">
        {/* Today's Reminders */}
        <div className="card card--warm card--interactive" onClick={() => navigate('/reminders')}>
          <div className="card__title">
            <span>⏰</span> Today's Reminders
          </div>
          {loading ? (
            <div className="skeleton" style={{ height: 40, width: '80%' }} />
          ) : reminders.length > 0 ? (
            <div>
              {reminders.slice(0, 3).map((r) => (
                <div key={r.id} className="reminder-item" style={{ marginBottom: 8, border: 'none', padding: '8px 0' }}>
                  <span>{r.is_medication ? '💊' : '📋'}</span>
                  <div className="reminder-item__content">
                    <div className="reminder-item__label">{r.label}</div>
                    <div className="reminder-item__time">{r.scheduled_time}</div>
                  </div>
                  <span className={`badge badge--${r.status}`}>{r.status}</span>
                </div>
              ))}
              {reminders.length > 3 && (
                <p style={{ color: 'var(--text-muted)', fontSize: 'var(--text-sm)' }}>
                  +{reminders.length - 3} more
                </p>
              )}
            </div>
          ) : (
            <p style={{ color: 'var(--text-muted)' }}>No reminders for today</p>
          )}
        </div>

        {/* Next Reminder */}
        <div className="card card--interactive" onClick={() => navigate('/reminders')}>
          <div className="card__title">
            <span>⏳</span> Coming Up Next
          </div>
          {loading ? (
            <div className="skeleton" style={{ height: 40, width: '80%' }} />
          ) : nextReminder ? (
            <div>
              <div className="reminder-item__label">{nextReminder.label}</div>
              <div className="reminder-item__time">
                {nextReminder.scheduled_date} at {nextReminder.scheduled_time}
              </div>
              {nextReminder.is_medication && <span className="badge badge--medication">💊 Medication</span>}
            </div>
          ) : (
            <p style={{ color: 'var(--text-muted)' }}>No upcoming reminders</p>
          )}
        </div>

        {/* Daily Check-in */}
        <div
          className={`card card--interactive ${
            checkin && checkin.status === 'pending' ? 'card--highlighted' : ''
          }`}
          onClick={() => navigate('/checkin')}
        >
          <div className="card__title">
            <span>💚</span> Daily Check-in
          </div>
          {loading ? (
            <div className="skeleton" style={{ height: 40, width: '80%' }} />
          ) : checkin && checkin.status === 'pending' ? (
            <p style={{ color: 'var(--sage-dark)', fontWeight: 600 }}>
              Ready for you! Tap to check in.
            </p>
          ) : checkin && checkin.status === 'completed' ? (
            <p style={{ color: 'var(--text-muted)' }}>
              ✅ Completed today. See you tomorrow!
            </p>
          ) : (
            <p style={{ color: 'var(--text-muted)' }}>Check-ins will appear here</p>
          )}
        </div>
      </div>

      {/* Help Button */}
      <div style={{ textAlign: 'center', marginTop: 'var(--space-2xl)' }} className="animate-fade-in-up stagger-3">
        <button
          className="btn btn--danger btn--large"
          onClick={handleHelp}
          disabled={voiceState === 'thinking'}
        >
          🆘 I Need Help
        </button>
        <p style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', marginTop: 'var(--space-sm)' }}>
          This will notify your trusted contacts. For emergencies, call your local emergency number.
        </p>
      </div>
    </div>
  );
}
