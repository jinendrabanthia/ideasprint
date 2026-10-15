import { useState, useEffect } from 'react';
import { useAuth } from '../AuthContext';
import api from '../api';

interface Contact {
  id: string;
  name: string;
  phone: string;
  relationship: string;
  is_emergency_primary: boolean;
}

export default function Settings() {
  const { user, signOut } = useAuth();
  const [fontSize, setFontSize] = useState<'normal' | 'large' | 'xlarge'>('large');
  const [highContrast, setHighContrast] = useState(false);
  const [speechRate, setSpeechRate] = useState('0.85');
  const [language, setLanguage] = useState('en-US');

  // Contacts
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [newContactName, setNewContactName] = useState('');
  const [newContactPhone, setNewContactPhone] = useState('');
  const [newContactRel, setNewContactRel] = useState('Daughter');
  const [showAddContact, setShowAddContact] = useState(false);
  const [saveStatus, setSaveStatus] = useState<string | null>(null);

  useEffect(() => {
    loadContacts();
    // Load local accessibility preferences
    const savedSize = localStorage.getItem('s_font_size') as any;
    if (savedSize) setFontSize(savedSize);
    const savedContrast = localStorage.getItem('s_contrast');
    if (savedContrast === 'true') setHighContrast(true);
  }, [user]);

  const loadContacts = async () => {
    if (!user?.profileId) return;
    try {
      const data = await api.getContacts(user.profileId);
      setContacts(data);
    } catch {
      // Mock initial contacts
      setContacts([
        {
          id: '1',
          name: 'Sarah Jenkins',
          phone: '+1 (555) 234-5678',
          relationship: 'Daughter',
          is_emergency_primary: true,
        },
      ]);
    }
  };

  const handleSavePreferences = () => {
    localStorage.setItem('s_font_size', fontSize);
    localStorage.setItem('s_contrast', highContrast ? 'true' : 'false');
    document.documentElement.setAttribute('data-font-size', fontSize);
    if (highContrast) {
      document.documentElement.classList.add('high-contrast');
    } else {
      document.documentElement.classList.remove('high-contrast');
    }

    setSaveStatus('Preferences saved successfully!');
    setTimeout(() => setSaveStatus(null), 3000);
  };

  const handleAddContact = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user?.profileId || !newContactName || !newContactPhone) return;

    try {
      const res = await api.createContact(user.profileId, {
        name: newContactName,
        phone: newContactPhone,
        relationship: newContactRel,
        is_emergency_primary: contacts.length === 0,
      });
      setContacts((prev) => [...prev, res]);
      setShowAddContact(false);
      setNewContactName('');
      setNewContactPhone('');
    } catch {
      const fallback: Contact = {
        id: Date.now().toString(),
        name: newContactName,
        phone: newContactPhone,
        relationship: newContactRel,
        is_emergency_primary: contacts.length === 0,
      };
      setContacts((prev) => [...prev, fallback]);
      setShowAddContact(false);
      setNewContactName('');
      setNewContactPhone('');
    }
  };

  const handleDeleteContact = async (id: string) => {
    if (!user?.profileId) return;
    try {
      await api.deleteContact(user.profileId, id);
      setContacts((prev) => prev.filter((c) => c.id !== id));
    } catch {
      setContacts((prev) => prev.filter((c) => c.id !== id));
    }
  };

  return (
    <div className="settings-page-container">
      <div className="page-header-row">
        <div>
          <h1>Accessibility & Settings</h1>
          <p className="page-subtitle">Customize Sahara to be as comfortable and readable as possible for your eyes and ears.</p>
        </div>
      </div>

      {saveStatus && (
        <div className="feedback-toast">
          <span>✓ {saveStatus}</span>
        </div>
      )}

      {/* Accessibility options */}
      <div className="settings-card">
        <h2>👁️ Visual & Audio Comfort</h2>

        <div className="setting-row">
          <div>
            <strong>Text Size</strong>
            <p className="setting-desc">Make all text and buttons easier to read</p>
          </div>
          <div className="font-size-selectors">
            <button
              type="button"
              className={`btn-toggle ${fontSize === 'normal' ? 'active' : ''}`}
              onClick={() => setFontSize('normal')}
            >
              Default
            </button>
            <button
              type="button"
              className={`btn-toggle ${fontSize === 'large' ? 'active' : ''}`}
              onClick={() => setFontSize('large')}
            >
              Large
            </button>
            <button
              type="button"
              className={`btn-toggle ${fontSize === 'xlarge' ? 'active' : ''}`}
              onClick={() => setFontSize('xlarge')}
            >
              Extra Large
            </button>
          </div>
        </div>

        <div className="setting-row">
          <div>
            <strong>High Contrast Mode</strong>
            <p className="setting-desc">Boost borders and contrast for sharper visibility</p>
          </div>
          <label className="toggle-switch">
            <input
              type="checkbox"
              checked={highContrast}
              onChange={(e) => setHighContrast(e.target.checked)}
            />
            <span className="slider" />
          </label>
        </div>

        <div className="setting-row">
          <div>
            <strong>Companion Speech Pace</strong>
            <p className="setting-desc">How fast Sahara speaks aloud</p>
          </div>
          <select value={speechRate} onChange={(e) => setSpeechRate(e.target.value)} className="select-input">
            <option value="0.75">Gentle & Slow (0.75x)</option>
            <option value="0.85">Recommended Senior Pace (0.85x)</option>
            <option value="1.0">Standard Speed (1.0x)</option>
          </select>
        </div>

        <div className="setting-row">
          <div>
            <strong>Companion Language</strong>
            <p className="setting-desc">Preferred language for speaking and replies</p>
          </div>
          <select value={language} onChange={(e) => setLanguage(e.target.value)} className="select-input">
            <option value="en-US">English (US)</option>
            <option value="en-GB">English (UK)</option>
            <option value="es-ES">Español</option>
            <option value="hi-IN">Hindi</option>
            <option value="fr-FR">Français</option>
          </select>
        </div>

        <button className="btn-primary" onClick={handleSavePreferences}>
          Save Accessibility Settings
        </button>
      </div>

      {/* Trusted Contacts */}
      <div className="settings-card">
        <div className="card-header-flex">
          <div>
            <h2>📞 Trusted & Emergency Contacts</h2>
            <p className="setting-desc">Family members or caregivers who will receive notifications and alerts.</p>
          </div>
          <button className="btn-secondary" onClick={() => setShowAddContact(true)}>
            ➕ Add Contact
          </button>
        </div>

        {contacts.length === 0 ? (
          <p className="empty-notice">No trusted contacts added yet. Add at least one family member or caregiver.</p>
        ) : (
          <div className="contacts-list">
            {contacts.map((c) => (
              <div key={c.id} className="contact-item-card">
                <div className="contact-info">
                  <strong>{c.name} {c.is_emergency_primary && <span className="primary-pill">Primary</span>}</strong>
                  <span className="contact-rel">{c.relationship} • {c.phone}</span>
                </div>
                <button
                  className="btn-delete-contact"
                  onClick={() => handleDeleteContact(c.id)}
                  aria-label="Remove contact"
                >
                  Remove
                </button>
              </div>
            ))}
          </div>
        )}

        {showAddContact && (
          <form onSubmit={handleAddContact} className="add-contact-subform">
            <h3>Add New Trusted Contact</h3>
            <div className="form-grid">
              <input
                type="text"
                placeholder="Full Name (e.g. Sarah Jenkins)"
                required
                value={newContactName}
                onChange={(e) => setNewContactName(e.target.value)}
              />
              <input
                type="tel"
                placeholder="Phone Number (e.g. +1 555-0192)"
                required
                value={newContactPhone}
                onChange={(e) => setNewContactPhone(e.target.value)}
              />
              <select value={newContactRel} onChange={(e) => setNewContactRel(e.target.value)}>
                <option value="Daughter">Daughter</option>
                <option value="Son">Son</option>
                <option value="Spouse">Spouse</option>
                <option value="Caregiver">Caregiver</option>
                <option value="Neighbor">Neighbor</option>
                <option value="Doctor">Doctor / Clinic</option>
              </select>
            </div>
            <div className="subform-buttons">
              <button type="button" className="btn-cancel" onClick={() => setShowAddContact(false)}>
                Cancel
              </button>
              <button type="submit" className="btn-primary">
                Save Contact
              </button>
            </div>
          </form>
        )}
      </div>

      {/* Safety & Compliance Card */}
      <div className="settings-card disclaimer-card">
        <h3>🛡️ Safety & Medical Scope Notice</h3>
        <p>
          Sahara AI is an assistive companion designed for daily support, reminders, and comfort. It does not provide medical diagnoses, clinical prescriptions, or real-time 911 emergency dispatch.
        </p>
        <p>
          Emergency simulations triggered within this application dispatch alerts to registered mock endpoints and caregiver dashboards for demonstration and verification purposes.
        </p>
      </div>

      {/* Account actions */}
      <div className="settings-card account-card">
        <h2>👤 Account</h2>
        <p>Signed in as: <strong>{user?.email}</strong> (Role: {user?.role})</p>
        <button className="btn-signout" onClick={signOut}>
          Sign Out
        </button>
      </div>
    </div>
  );
}
