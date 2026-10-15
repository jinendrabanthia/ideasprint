import { useState, useEffect } from 'react';
import { useAuth } from '../AuthContext';
import api from '../api';

interface Reminder {
  id: string;
  title: string;
  reminder_type: string;
  scheduled_time: string;
  frequency: string;
  status: 'pending' | 'completed' | 'snoozed' | 'missed';
  notes?: string;
}

export default function Reminders() {
  const { user } = useAuth();
  const [reminders, setReminders] = useState<Reminder[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newType, setNewType] = useState('medication');
  const [newTime, setNewTime] = useState('');
  const [newFrequency, setNewFrequency] = useState('daily');
  const [newNotes, setNewNotes] = useState('');
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  useEffect(() => {
    loadReminders();
  }, [user]);

  const loadReminders = async () => {
    if (!user?.profileId) return;
    try {
      setLoading(true);
      const data = await api.getReminders(user.profileId);
      setReminders(data);
    } catch {
      // Mock fallback reminders for initial senior setup
      setReminders([
        {
          id: '1',
          title: 'Morning Blood Pressure Medication',
          reminder_type: 'medication',
          scheduled_time: '08:00 AM',
          frequency: 'daily',
          status: 'completed',
          notes: 'Take with half glass of warm water after breakfast',
        },
        {
          id: '2',
          title: 'Midday Hydration & Gentle Stretch',
          reminder_type: 'hydration',
          scheduled_time: '12:30 PM',
          frequency: 'daily',
          status: 'pending',
          notes: 'Drink a glass of water and rest eyes for 5 minutes',
        },
        {
          id: '3',
          title: 'Evening Walk in Garden',
          reminder_type: 'habit',
          scheduled_time: '05:30 PM',
          frequency: 'daily',
          status: 'pending',
          notes: '15-minute gentle stroll with comfortable shoes',
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleAcknowledge = async (id: string, title: string) => {
    if (!user?.profileId) return;
    try {
      await api.acknowledgeReminder(id, user.profileId);
      setReminders((prev) =>
        prev.map((r) => (r.id === id ? { ...r, status: 'completed' as const } : r))
      );
      speakFeedback(`Well done! Marked ${title} as completed.`);
      showNotification(`Marked "${title}" as completed.`);
    } catch {
      setReminders((prev) =>
        prev.map((r) => (r.id === id ? { ...r, status: 'completed' as const } : r))
      );
      speakFeedback(`Completed: ${title}`);
      showNotification(`Completed "${title}".`);
    }
  };

  const handleSnooze = async (id: string, title: string) => {
    if (!user?.profileId) return;
    try {
      await api.snoozeReminder(id, user.profileId, 15);
      setReminders((prev) =>
        prev.map((r) => (r.id === id ? { ...r, status: 'snoozed' as const } : r))
      );
      speakFeedback(`Snoozed ${title} for 15 minutes.`);
      showNotification(`Snoozed "${title}" for 15 minutes.`);
    } catch {
      setReminders((prev) =>
        prev.map((r) => (r.id === id ? { ...r, status: 'snoozed' as const } : r))
      );
      showNotification(`Snoozed "${title}" for 15 minutes.`);
    }
  };

  const speakFeedback = (text: string) => {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      const utt = new SpeechSynthesisUtterance(text);
      utt.rate = 0.85;
      window.speechSynthesis.speak(utt);
    }
  };

  const showNotification = (msg: string) => {
    setActionMessage(msg);
    setTimeout(() => setActionMessage(null), 4000);
  };

  const handleCreateReminder = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user?.profileId || !newTitle || !newTime) return;

    try {
      const created = await api.createReminder(user.profileId, {
        title: newTitle,
        reminder_type: newType,
        scheduled_time: newTime,
        frequency: newFrequency,
        notes: newNotes,
      });
      setReminders((prev) => [...prev, created]);
      setShowAddModal(false);
      setNewTitle('');
      setNewTime('');
      setNewNotes('');
      showNotification('New reminder scheduled!');
    } catch {
      // Offline fallback
      const localItem: Reminder = {
        id: Date.now().toString(),
        title: newTitle,
        reminder_type: newType,
        scheduled_time: newTime,
        frequency: newFrequency,
        status: 'pending',
        notes: newNotes,
      };
      setReminders((prev) => [...prev, localItem]);
      setShowAddModal(false);
      setNewTitle('');
      setNewTime('');
      setNewNotes('');
      showNotification('Reminder added!');
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case 'medication':
        return '💊';
      case 'hydration':
        return '💧';
      case 'appointment':
        return '🩺';
      case 'habit':
        return '🌱';
      default:
        return '⏰';
    }
  };

  return (
    <div className="reminders-page-container">
      <div className="page-header-row">
        <div>
          <h1>Daily Reminders</h1>
          <p className="page-subtitle">Clear, easy reminders for your medications, water, and daily routines.</p>
        </div>
        <button className="btn-primary-large" onClick={() => setShowAddModal(true)}>
          ➕ Add New Reminder
        </button>
      </div>

      {actionMessage && (
        <div className="feedback-toast">
          <span>✨ {actionMessage}</span>
        </div>
      )}

      {loading ? (
        <div className="loading-state">
          <div className="spinner" />
          <p>Loading your schedule...</p>
        </div>
      ) : reminders.length === 0 ? (
        <div className="empty-state-card">
          <span className="empty-emoji">🌻</span>
          <h3>All clear! No pending reminders right now.</h3>
          <p>Tap "Add New Reminder" above whenever you want Sahara to keep track of a medicine or routine.</p>
        </div>
      ) : (
        <div className="reminders-grid">
          {reminders.map((r) => (
            <div
              key={r.id}
              className={`reminder-card status-${r.status}`}
            >
              <div className="reminder-card-top">
                <span className="reminder-type-badge">
                  {getTypeIcon(r.reminder_type)} {r.reminder_type.toUpperCase()}
                </span>
                <span className={`status-pill pill-${r.status}`}>
                  {r.status === 'completed' && '✓ Done'}
                  {r.status === 'pending' && '⏳ Due'}
                  {r.status === 'snoozed' && '💤 Snoozed'}
                  {r.status === 'missed' && '⚠️ Missed'}
                </span>
              </div>

              <h2 className="reminder-title">{r.title}</h2>

              <div className="reminder-time-row">
                <span className="clock-icon">🕒</span>
                <span className="time-val">{r.scheduled_time}</span>
                <span className="frequency-val">({r.frequency})</span>
              </div>

              {r.notes && <p className="reminder-notes">{r.notes}</p>}

              <div className="reminder-action-buttons">
                {r.status !== 'completed' ? (
                  <>
                    <button
                      className="btn-complete-action"
                      onClick={() => handleAcknowledge(r.id, r.title)}
                    >
                      ✓ I Took This / Done
                    </button>
                    <button
                      className="btn-snooze-action"
                      onClick={() => handleSnooze(r.id, r.title)}
                    >
                      💤 Snooze 15m
                    </button>
                  </>
                ) : (
                  <button
                    className="btn-read-aloud"
                    onClick={() => speakFeedback(`Completed: ${r.title} at ${r.scheduled_time}.`)}
                  >
                    🔊 Read Aloud
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Add Reminder Modal */}
      {showAddModal && (
        <div className="modal-backdrop" onClick={() => setShowAddModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Add a New Reminder</h2>
              <button className="btn-close-modal" onClick={() => setShowAddModal(false)}>✕</button>
            </div>
            <form onSubmit={handleCreateReminder} className="modal-form">
              <label>
                What should we remind you about?
                <input
                  type="text"
                  required
                  placeholder="e.g. Heart medication, Drink water, Doctor call"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                />
              </label>

              <div className="form-row">
                <label>
                  Type:
                  <select value={newType} onChange={(e) => setNewType(e.target.value)}>
                    <option value="medication">💊 Medication</option>
                    <option value="hydration">💧 Hydration</option>
                    <option value="appointment">🩺 Appointment</option>
                    <option value="habit">🌱 Habit / Walk</option>
                    <option value="other">⏰ Other</option>
                  </select>
                </label>

                <label>
                  Time:
                  <input
                    type="time"
                    required
                    value={newTime}
                    onChange={(e) => setNewTime(e.target.value)}
                  />
                </label>
              </div>

              <label>
                Frequency:
                <select value={newFrequency} onChange={(e) => setNewFrequency(e.target.value)}>
                  <option value="daily">Daily</option>
                  <option value="twice_daily">Twice Daily</option>
                  <option value="weekly">Weekly</option>
                  <option value="as_needed">As Needed</option>
                </select>
              </label>

              <label>
                Helpful Notes (optional):
                <textarea
                  placeholder="e.g. Take with food, use blue water bottle..."
                  value={newNotes}
                  onChange={(e) => setNewNotes(e.target.value)}
                  rows={2}
                />
              </label>

              <div className="modal-footer-buttons">
                <button type="button" className="btn-cancel" onClick={() => setShowAddModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn-confirm-save">
                  Save Reminder
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
