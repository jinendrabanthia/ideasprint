import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../AuthContext';
import api from '../api';

const STEPS = [
  {
    icon: '🌻',
    title: 'Welcome to Sahara',
    description:
      'Sahara is your friendly daily companion. I can help you remember medications, schedule appointments, and check in on how you\'re doing each day.\n\nI\'m here to support you — but I\'m not a doctor or emergency service. For medical emergencies, always call your local emergency number.',
  },
  {
    icon: '🎤',
    title: 'Talk to Me',
    description:
      'You can talk to Sahara using your voice or by typing. Just tap the talk button on the home screen.\n\nI\'ll listen carefully and respond with both voice and text so you can hear me and read along.',
  },
  {
    icon: '👨‍👩‍👧',
    title: 'Your Trusted Circle',
    description:
      'You can add trusted contacts — family members or caregivers who you want to be notified if you need help.\n\nYou control who has access. You can add or remove contacts anytime from Settings.',
  },
  {
    icon: '🔒',
    title: 'Your Privacy Matters',
    description:
      'Your data stays private. Caregivers can only see information you authorize them to access.\n\nSahara doesn\'t store voice recordings and keeps minimal notes about your conversations.',
  },
  {
    icon: '⚙️',
    title: 'Set Your Preferences',
    description: 'Let\'s make Sahara comfortable for you.',
    hasSettings: true,
  },
];

export default function Onboarding() {
  const [step, setStep] = useState(0);
  const [speechRate, setSpeechRate] = useState(1.0);
  const [language, setLanguage] = useState('en');
  const [saving, setSaving] = useState(false);
  const navigate = useNavigate();
  const { user } = useAuth();

  const current = STEPS[step];

  const handleFinish = async () => {
    setSaving(true);
    try {
      await api.updateProfile({
        speech_rate: speechRate,
        language,
        onboarding_complete: true,
      });
      navigate('/');
    } catch {
      navigate('/');
    }
  };

  const testSpeech = () => {
    if ('speechSynthesis' in window) {
      const utterance = new SpeechSynthesisUtterance(
        'Hello! I\'m Sahara, your daily companion. How are you today?'
      );
      utterance.rate = speechRate;
      utterance.lang = language === 'hi' ? 'hi-IN' : 'en-US';
      window.speechSynthesis.cancel();
      window.speechSynthesis.speak(utterance);
    }
  };

  const testMicrophone = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      stream.getTracks().forEach((t) => t.stop());
      alert('✅ Microphone is working!');
    } catch {
      alert('❌ Microphone access denied. You can still type to interact.');
    }
  };

  return (
    <div className="auth-page" style={{ flexDirection: 'column', gap: 'var(--space-xl)' }}>
      <div className="onboarding-progress">
        {STEPS.map((_, i) => (
          <div
            key={i}
            className={`onboarding-dot ${
              i === step ? 'onboarding-dot--active' : i < step ? 'onboarding-dot--done' : ''
            }`}
          />
        ))}
      </div>

      <div className="auth-card" style={{ maxWidth: 520 }}>
        <div className="onboarding-step" key={step}>
          <div className="onboarding-step__icon">{current.icon}</div>
          <h1 className="onboarding-step__title">{current.title}</h1>
          <p className="onboarding-step__description" style={{ whiteSpace: 'pre-line' }}>
            {current.description}
          </p>

          {current.hasSettings && (
            <div style={{ textAlign: 'left', marginBottom: 'var(--space-xl)' }}>
              <div className="form-group">
                <label className="form-label">Language</label>
                <select
                  className="form-input"
                  value={language}
                  onChange={(e) => setLanguage(e.target.value)}
                >
                  <option value="en">English</option>
                  <option value="hi">हिन्दी (Hindi)</option>
                  <option value="es">Español (Spanish)</option>
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">Speech Speed</label>
                <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-md)' }}>
                  <span style={{ fontSize: 'var(--text-sm)' }}>Slower</span>
                  <input
                    type="range"
                    min={0.5}
                    max={1.5}
                    step={0.1}
                    value={speechRate}
                    onChange={(e) => setSpeechRate(parseFloat(e.target.value))}
                    style={{ flex: 1 }}
                    aria-label="Speech rate"
                  />
                  <span style={{ fontSize: 'var(--text-sm)' }}>Faster</span>
                </div>
              </div>

              <div style={{ display: 'flex', gap: 'var(--space-md)', marginTop: 'var(--space-md)' }}>
                <button className="btn btn--secondary" onClick={testSpeech} type="button" style={{ flex: 1 }}>
                  🔊 Test Speaker
                </button>
                <button className="btn btn--secondary" onClick={testMicrophone} type="button" style={{ flex: 1 }}>
                  🎤 Test Microphone
                </button>
              </div>
            </div>
          )}

          <div style={{ display: 'flex', gap: 'var(--space-md)', justifyContent: 'center' }}>
            {step > 0 && (
              <button className="btn btn--ghost" onClick={() => setStep(step - 1)}>
                ← Back
              </button>
            )}
            {step < STEPS.length - 1 ? (
              <button className="btn btn--primary btn--large" onClick={() => setStep(step + 1)}>
                Continue →
              </button>
            ) : (
              <button
                className="btn btn--primary btn--large"
                onClick={handleFinish}
                disabled={saving}
              >
                {saving ? 'Setting up...' : "Let's Get Started! 🌟"}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
