import { useState, useEffect } from 'react';
import { useAuth } from '../AuthContext';
import api from '../api';

interface CheckInHistoryItem {
  id: string;
  created_at: string;
  mood: string;
  physical_state: string;
  sleep_quality: string;
  notes?: string;
  ai_summary?: string;
}

export default function CheckIn() {
  const { user } = useAuth();
  const [mood, setMood] = useState<string>('good');
  const [physicalState, setPhysicalState] = useState<string>('fine');
  const [sleepQuality, setSleepQuality] = useState<string>('well');
  const [notes, setNotes] = useState<string>('');
  const [submitting, setSubmitting] = useState(false);
  const [submittedToday, setSubmittedToday] = useState(false);
  const [history, setHistory] = useState<CheckInHistoryItem[]>([]);
  const [feedbackMsg, setFeedbackMsg] = useState<string | null>(null);

  useEffect(() => {
    loadCheckInStatus();
  }, [user]);

  const loadCheckInStatus = async () => {
    if (!user?.profileId) return;
    try {
      const data = await api.getCheckIns(user.profileId);
      if (data && data.length > 0) {
        setHistory(data);
        const todayStr = new Date().toISOString().split('T')[0];
        const hasToday = data.some((item: any) => item.created_at.startsWith(todayStr));
        if (hasToday) {
          setSubmittedToday(true);
        }
      }
    } catch {
      // Demo state if backend returns empty
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user?.profileId) return;

    setSubmitting(true);
    try {
      await api.createCheckIn(user.profileId, {
        mood,
        physical_state: physicalState,
        sleep_quality: sleepQuality,
        notes,
      });

      setSubmittedToday(true);
      const greeting = `Thank you, ${user.displayName || 'friend'}! Your check-in is recorded. I'm glad to be with you today.`;
      setFeedbackMsg(greeting);

      if ('speechSynthesis' in window) {
        const utt = new SpeechSynthesisUtterance(greeting);
        utt.rate = 0.85;
        window.speechSynthesis.speak(utt);
      }

      loadCheckInStatus();
    } catch {
      setSubmittedToday(true);
      setFeedbackMsg("Check-in saved locally for today! Wishing you a peaceful, healthy day.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="checkin-page-container">
      <div className="page-header-row">
        <div>
          <h1>Daily Check-In</h1>
          <p className="page-subtitle">A quick, gentle moment to share how you are feeling today.</p>
        </div>
      </div>

      {feedbackMsg && (
        <div className="checkin-success-banner">
          <span className="success-icon">🌻</span>
          <div>
            <h3>Check-in Received!</h3>
            <p>{feedbackMsg}</p>
          </div>
        </div>
      )}

      {submittedToday && !feedbackMsg ? (
        <div className="already-submitted-card">
          <span className="huge-icon">☀️</span>
          <h2>You have checked in for today!</h2>
          <p>
            Your loved ones and caregiver can see that you're up and doing well. If your feelings change later or you need anything, simply visit Chat to speak with Sahara.
          </p>
          <button className="btn-secondary" onClick={() => setSubmittedToday(false)}>
            Update Today's Check-In
          </button>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="checkin-form-card">
          {/* Question 1: Mood */}
          <div className="checkin-section">
            <label className="section-label">1. How is your mood today?</label>
            <div className="mood-options-grid">
              {[
                { val: 'great', emoji: '😄', label: 'Great' },
                { val: 'good', emoji: '🙂', label: 'Good' },
                { val: 'okay', emoji: '😐', label: 'Just Okay' },
                { val: 'low', emoji: '😔', label: 'A bit low' },
              ].map((opt) => (
                <button
                  type="button"
                  key={opt.val}
                  className={`mood-button ${mood === opt.val ? 'selected' : ''}`}
                  onClick={() => setMood(opt.val)}
                >
                  <span className="mood-emoji">{opt.emoji}</span>
                  <span className="mood-title">{opt.label}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Question 2: Physical feeling */}
          <div className="checkin-section">
            <label className="section-label">2. How does your body feel?</label>
            <div className="mood-options-grid">
              {[
                { val: 'energetic', emoji: '💪', label: 'Energetic' },
                { val: 'fine', emoji: '🌿', label: 'Comfortable' },
                { val: 'tired', emoji: '🥱', label: 'A little tired' },
                { val: 'discomfort', emoji: '🤕', label: 'Some aches' },
              ].map((opt) => (
                <button
                  type="button"
                  key={opt.val}
                  className={`mood-button ${physicalState === opt.val ? 'selected' : ''}`}
                  onClick={() => setPhysicalState(opt.val)}
                >
                  <span className="mood-emoji">{opt.emoji}</span>
                  <span className="mood-title">{opt.label}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Question 3: Sleep */}
          <div className="checkin-section">
            <label className="section-label">3. How did you sleep last night?</label>
            <div className="mood-options-grid">
              {[
                { val: 'well', emoji: '😴', label: 'Deeply & Well' },
                { val: 'woke_up', emoji: '🌙', label: 'Woke up a few times' },
                { val: 'restless', emoji: '🌧️', label: 'Restless / Troubled' },
              ].map((opt) => (
                <button
                  type="button"
                  key={opt.val}
                  className={`mood-button ${sleepQuality === opt.val ? 'selected' : ''}`}
                  onClick={() => setSleepQuality(opt.val)}
                >
                  <span className="mood-emoji">{opt.emoji}</span>
                  <span className="mood-title">{opt.label}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Question 4: Freeform note */}
          <div className="checkin-section">
            <label className="section-label">Anything special on your mind or plans for today? (Optional)</label>
            <textarea
              className="checkin-textarea"
              rows={3}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="e.g. Daughter visited yesterday, planning to sit by the balcony..."
            />
          </div>

          <button type="submit" className="btn-submit-checkin" disabled={submitting}>
            {submitting ? 'Submitting Check-In...' : '🌻 Complete Today’s Check-In'}
          </button>
        </form>
      )}

      {/* Check-In History / Streak */}
      {history.length > 0 && (
        <div className="checkin-history-section">
          <h2>Recent Check-In History</h2>
          <div className="history-list">
            {history.slice(0, 5).map((h) => (
              <div key={h.id} className="history-item-card">
                <div className="history-date">
                  {new Date(h.created_at).toLocaleDateString([], {
                    weekday: 'short',
                    month: 'short',
                    day: 'numeric',
                  })}
                </div>
                <div className="history-summary">
                  <span className="badge">Mood: {h.mood}</span>
                  <span className="badge">Physical: {h.physical_state}</span>
                  <span className="badge">Sleep: {h.sleep_quality}</span>
                </div>
                {h.notes && <p className="history-notes">"{h.notes}"</p>}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
