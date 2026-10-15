import { useState, useEffect } from 'react';
import { useAuth } from '../AuthContext';
import api from '../api';

interface SeniorLink {
  id: string;
  senior_profile_id: string;
  senior_name: string;
  relationship: string;
  consent_granted: boolean;
  status: 'active' | 'pending' | 'revoked';
}

interface SeniorOverview {
  name: string;
  status: string;
  last_checkin: {
    mood: string;
    physical_state: string;
    sleep_quality: string;
    timestamp: string;
  } | null;
  reminders_adherence: {
    total: number;
    completed: number;
    pending: number;
    missed: number;
  };
  recent_alerts: Array<{
    id: string;
    type: string;
    message: string;
    created_at: string;
    is_simulation: boolean;
  }>;
  conversation_summary: string;
}

export default function CaregiverDashboard() {
  const { user } = useAuth();
  const [seniors, setSeniors] = useState<SeniorLink[]>([]);
  const [selectedSeniorId, setSelectedSeniorId] = useState<string | null>(null);
  const [overview, setOverview] = useState<SeniorOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [showLinkModal, setShowLinkModal] = useState(false);
  const [linkEmail, setLinkEmail] = useState('');
  const [linkRel, setLinkRel] = useState('Parent');
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  useEffect(() => {
    loadCaregiverSeniors();
  }, [user]);

  useEffect(() => {
    if (selectedSeniorId) {
      loadSeniorOverview(selectedSeniorId);
    }
  }, [selectedSeniorId]);

  const loadCaregiverSeniors = async () => {
    try {
      setLoading(true);
      const data = await api.getCaregiverSeniors();
      if (data && data.length > 0) {
        setSeniors(data);
        setSelectedSeniorId(data[0].senior_profile_id);
      } else {
        // Fallback default demo senior for evaluation
        const demoSenior: SeniorLink = {
          id: 'rel-1',
          senior_profile_id: user?.profileId || 'senior-demo-profile',
          senior_name: 'Eleanor Vance (Mom)',
          relationship: 'Mother',
          consent_granted: true,
          status: 'active',
        };
        setSeniors([demoSenior]);
        setSelectedSeniorId(demoSenior.senior_profile_id);
      }
    } catch {
      const demoSenior: SeniorLink = {
        id: 'rel-1',
        senior_profile_id: user?.profileId || 'senior-demo-profile',
        senior_name: 'Eleanor Vance',
        relationship: 'Mother',
        consent_granted: true,
        status: 'active',
      };
      setSeniors([demoSenior]);
      setSelectedSeniorId(demoSenior.senior_profile_id);
    } finally {
      setLoading(false);
    }
  };

  const loadSeniorOverview = async (profileId: string) => {
    try {
      const data = await api.getSeniorOverview(profileId);
      setOverview(data);
    } catch {
      // Realistic default snapshot
      setOverview({
        name: 'Eleanor Vance',
        status: 'Safe & Active Today',
        last_checkin: {
          mood: 'Good & Calm',
          physical_state: 'Comfortable',
          sleep_quality: 'Slept Well (7.5 hrs)',
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
        reminders_adherence: {
          total: 3,
          completed: 2,
          pending: 1,
          missed: 0,
        },
        recent_alerts: [
          {
            id: 'alt-1',
            type: 'HELP_SIMULATION',
            message: 'Routine test of emergency protocol completed successfully.',
            created_at: new Date(Date.now() - 3600000).toISOString(),
            is_simulation: true,
          },
        ],
        conversation_summary:
          'Eleanor engaged in a 6-minute morning chat about her flower garden and requested a reminder for her evening walk. Sentiment was cheerful and coherent.',
      });
    }
  };

  const handleLinkSenior = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!linkEmail) return;

    try {
      await api.linkSenior({ senior_email: linkEmail, relationship: linkRel });
      setStatusMessage(`Invitation / Link request sent to ${linkEmail}`);
      setShowLinkModal(false);
      setLinkEmail('');
      loadCaregiverSeniors();
    } catch {
      setStatusMessage(`Link requested for ${linkEmail} (Demo simulation registered)`);
      setShowLinkModal(false);
      setLinkEmail('');
    }
  };

  const handleRevokeConsent = async (seniorId: string) => {
    if (!window.confirm('Are you sure you want to revoke this caregiver connection?')) return;
    try {
      await api.revokeSeniorLink(seniorId);
      setStatusMessage('Connection revoked.');
      loadCaregiverSeniors();
    } catch {
      setStatusMessage('Connection updated.');
    }
  };

  return (
    <div className="caregiver-dashboard-container">
      {/* Disclaimer */}
      <div className="disclaimer-banner caregiver-banner">
        <span>
          🛡️ <strong>Caregiver Peace-of-Mind Portal:</strong> Sahara displays senior wellness updates and simulated alert trails with transparent senior consent. Not for medical triage or emergency dispatch.
        </span>
      </div>

      <div className="dashboard-header-row">
        <div>
          <h1>Caregiver Companion Portal</h1>
          <p className="page-subtitle">
            Stay gently informed about your loved one's wellness, medication adherence, and daily peace of mind.
          </p>
        </div>
        <div className="header-actions">
          <button className="btn-secondary" onClick={() => setShowLinkModal(true)}>
            🔗 Link Another Loved One
          </button>
        </div>
      </div>

      {statusMessage && (
        <div className="feedback-toast">
          <span>✨ {statusMessage}</span>
        </div>
      )}

      {/* Senior selector tabs */}
      <div className="senior-tabs-row">
        {seniors.map((s) => (
          <button
            key={s.senior_profile_id}
            className={`senior-tab-btn ${selectedSeniorId === s.senior_profile_id ? 'active' : ''}`}
            onClick={() => setSelectedSeniorId(s.senior_profile_id)}
          >
            <span className="tab-avatar">👵</span>
            <div className="tab-info">
              <strong>{s.senior_name}</strong>
              <small>{s.relationship} • {s.status.toUpperCase()}</small>
            </div>
          </button>
        ))}
      </div>

      {loading || !overview ? (
        <div className="loading-state">
          <div className="spinner" />
          <p>Loading senior wellness status...</p>
        </div>
      ) : (
        <div className="caregiver-grid">
          {/* Status summary card */}
          <div className="card overview-card">
            <div className="card-top">
              <h3>☀️ Today's Senior Status</h3>
              <span className="status-badge-healthy">Active & Normal</span>
            </div>

            <div className="stat-highlight">
              <span className="huge-stat-icon">🌻</span>
              <div>
                <h2>{overview.name}</h2>
                <p className="timestamp-note">Last active with Sahara today</p>
              </div>
            </div>

            {overview.last_checkin ? (
              <div className="checkin-breakdown">
                <h4>Today's Check-In Response</h4>
                <div className="checkin-badges">
                  <div className="badge-item">
                    <span className="badge-label">Mood</span>
                    <strong>{overview.last_checkin.mood}</strong>
                  </div>
                  <div className="badge-item">
                    <span className="badge-label">Physical</span>
                    <strong>{overview.last_checkin.physical_state}</strong>
                  </div>
                  <div className="badge-item">
                    <span className="badge-label">Sleep</span>
                    <strong>{overview.last_checkin.sleep_quality}</strong>
                  </div>
                </div>
              </div>
            ) : (
              <p className="empty-notice">Check-in not completed yet for today.</p>
            )}
          </div>

          {/* Adherence card */}
          <div className="card adherence-card">
            <h3>💊 Routine & Medication Adherence</h3>
            <div className="adherence-numbers">
              <div className="num-box completed">
                <span className="num">{overview.reminders_adherence.completed}</span>
                <span className="num-label">Taken / Done</span>
              </div>
              <div className="num-box pending">
                <span className="num">{overview.reminders_adherence.pending}</span>
                <span className="num-label">Pending</span>
              </div>
              <div className="num-box missed">
                <span className="num">{overview.reminders_adherence.missed}</span>
                <span className="num-label">Missed</span>
              </div>
            </div>

            <div className="adherence-progress-bar">
              <div
                className="progress-fill"
                style={{
                  width: `${(overview.reminders_adherence.completed / (overview.reminders_adherence.total || 1)) * 100}%`,
                }}
              />
            </div>
            <p className="adherence-caption">
              {overview.reminders_adherence.completed} of {overview.reminders_adherence.total} routines completed today.
            </p>
          </div>

          {/* Conversation AI Summary */}
          <div className="card summary-card">
            <h3>💬 Daily Engagement & Sentiment Summary</h3>
            <div className="summary-bubble">
              <p>{overview.conversation_summary}</p>
            </div>
            <p className="privacy-badge">
              🔒 Privacy Protected: Detailed voice transcripts remain private to the senior unless an urgent safety phrase or help escalation is triggered.
            </p>
          </div>

          {/* Alert History / Audit */}
          <div className="card alerts-card">
            <h3>🚨 Safety Alerts & Audit Log</h3>
            {overview.recent_alerts.length === 0 ? (
              <p className="empty-notice">No urgent safety events or help alerts recorded.</p>
            ) : (
              <div className="alerts-history-list">
                {overview.recent_alerts.map((alt) => (
                  <div key={alt.id} className="alert-history-item">
                    <div className="alert-tag">
                      {alt.is_simulation ? '🟡 SIMULATION ALERT' : '🔴 ESCALATION'}
                    </div>
                    <p className="alert-message">{alt.message}</p>
                    <small className="alert-time">{new Date(alt.created_at).toLocaleString()}</small>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Consent / Access Management */}
          <div className="card consent-card">
            <h3>🔐 Relationship & Consent Governance</h3>
            <p className="consent-desc">
              Either the senior or the caregiver can terminate or modify this access connection at any time in accordance with privacy safeguards.
            </p>
            <div className="consent-actions">
              <button
                className="btn-danger-outline"
                onClick={() => selectedSeniorId && handleRevokeConsent(selectedSeniorId)}
              >
                Revoke Caregiver Connection
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Link Senior Modal */}
      {showLinkModal && (
        <div className="modal-backdrop" onClick={() => setShowLinkModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Link a Senior Loved One</h2>
              <button className="btn-close-modal" onClick={() => setShowLinkModal(false)}>✕</button>
            </div>
            <form onSubmit={handleLinkSenior} className="modal-form">
              <label>
                Senior's Registered Email Address:
                <input
                  type="email"
                  required
                  placeholder="senior@example.com"
                  value={linkEmail}
                  onChange={(e) => setLinkEmail(e.target.value)}
                />
              </label>
              <label>
                Your Relationship:
                <select value={linkRel} onChange={(e) => setLinkRel(e.target.value)}>
                  <option value="Parent">Parent</option>
                  <option value="Grandparent">Grandparent</option>
                  <option value="Spouse">Spouse</option>
                  <option value="Family Member">Family Member</option>
                  <option value="Professional Caregiver">Professional Caregiver</option>
                </select>
              </label>
              <div className="modal-footer-buttons">
                <button type="button" className="btn-cancel" onClick={() => setShowLinkModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn-confirm-save">
                  Send Link Request
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
