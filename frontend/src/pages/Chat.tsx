import { useState, useEffect, useRef } from 'react';
import { useAuth } from '../AuthContext';
import api from '../api';

interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  created_at: string;
  audio_url?: string;
}

export default function Chat() {
  const { user } = useAuth();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [voiceState, setVoiceState] = useState<'idle' | 'listening' | 'processing' | 'speaking'>('idle');
  const [isSimulatingHelp, setIsSimulatingHelp] = useState(false);
  const [helpBanner, setHelpBanner] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const recognitionRef = useRef<any>(null);

  useEffect(() => {
    loadConversation();
  }, [user]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, voiceState]);

  const loadConversation = async () => {
    if (!user?.profileId) return;
    try {
      const history = await api.getConversationHistory(user.profileId);
      if (history && history.length > 0) {
        setMessages(history);
      } else {
        setMessages([
          {
            id: 'welcome',
            role: 'assistant',
            content: `Hello ${user.displayName || 'there'}! I am Sahara, your daily companion. How are you feeling today? Tap the microphone button or pick an option below to talk with me.`,
            created_at: new Date().toISOString(),
          },
        ]);
      }
    } catch {
      setMessages([
        {
          id: 'welcome-default',
          role: 'assistant',
          content: `Hello ${user?.displayName || 'friend'}! I am Sahara, your daily companion. How can I help you today?`,
          created_at: new Date().toISOString(),
        },
      ]);
    }
  };

  const speakText = (text: string) => {
    if (!('speechSynthesis' in window)) return;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.85; // Calmer, clearer rate for seniors
    utterance.pitch = 1.0;
    utterance.onstart = () => setVoiceState('speaking');
    utterance.onend = () => setVoiceState('idle');
    utterance.onerror = () => setVoiceState('idle');
    window.speechSynthesis.speak(utterance);
  };

  const handleSend = async (textToSend?: string) => {
    const text = (textToSend || input).trim();
    if (!text || !user?.profileId) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: text,
      created_at: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setVoiceState('processing');

    try {
      const response = await api.sendMessage(user.profileId, text);
      const assistantMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.reply,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMsg]);
      speakText(response.reply);
    } catch {
      const fallbackMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: "I'm right here with you. I couldn't reach the server just now, but I heard what you said. How else can I assist?",
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, fallbackMsg]);
      setVoiceState('idle');
    }
  };

  const toggleListening = () => {
    if (voiceState === 'listening') {
      recognitionRef.current?.stop();
      setVoiceState('idle');
      return;
    }

    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      alert('Speech recognition is not supported in this browser. You can type your message in the box below!');
      return;
    }

    try {
      const recognition = new SpeechRecognition();
      recognitionRef.current = recognition;
      recognition.lang = 'en-US';
      recognition.interimResults = false;
      recognition.maxAlternatives = 1;

      recognition.onstart = () => {
        setVoiceState('listening');
      };

      recognition.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        if (transcript) {
          handleSend(transcript);
        }
      };

      recognition.onerror = () => {
        setVoiceState('idle');
      };

      recognition.onend = () => {
        setVoiceState('idle');
      };

      recognition.start();
    } catch {
      setVoiceState('idle');
    }
  };

  const handleSimulateHelp = async () => {
    if (!user?.profileId) return;
    setIsSimulatingHelp(true);
    try {
      await api.triggerHelp(user.profileId, 'Senior pressed the Help & Safety button in conversation.');
      setHelpBanner('Help Alert Dispatched (Simulation): Caregivers and trusted contacts have been notified with high priority.');
      setTimeout(() => setHelpBanner(null), 8000);
    } catch {
      setHelpBanner('Help Alert Simulation active: Emergency protocol demonstrated.');
      setTimeout(() => setHelpBanner(null), 6000);
    } finally {
      setIsSimulatingHelp(false);
    }
  };

  return (
    <div className="chat-container">
      {/* Non-clinical disclaimer banner */}
      <div className="disclaimer-banner">
        <span>⚠️ Sahara is an AI companion for senior daily care, not a doctor or emergency service. In an urgent medical emergency, call 911 or your local emergency line immediately.</span>
      </div>

      {helpBanner && (
        <div className="emergency-alert-banner">
          <span>🚨 {helpBanner}</span>
          <button onClick={() => setHelpBanner(null)}>Dismiss</button>
        </div>
      )}

      {/* Voice companion avatar and status */}
      <div className="companion-header-card">
        <div className={`companion-orb orb-${voiceState}`}>
          <span className="orb-emoji">
            {voiceState === 'listening' ? '🎙️' : voiceState === 'speaking' ? '🗣️' : voiceState === 'processing' ? '⏳' : '🌻'}
          </span>
        </div>
        <div className="companion-meta">
          <h2>Sahara Companion</h2>
          <p className="voice-status-text">
            {voiceState === 'listening' && 'Listening attentively... speak naturally'}
            {voiceState === 'processing' && 'Thinking and preparing response...'}
            {voiceState === 'speaking' && 'Speaking to you...'}
            {voiceState === 'idle' && 'Ready to chat with you'}
          </p>
        </div>
        <button
          className="btn-help-sim"
          onClick={handleSimulateHelp}
          disabled={isSimulatingHelp}
          title="Demonstrates safety alert escalation to trusted contacts"
        >
          {isSimulatingHelp ? 'Alerting...' : '🚨 Request Help (Simulation)'}
        </button>
      </div>

      {/* Message transcript list */}
      <div className="chat-messages-card">
        <div className="messages-scroll">
          {messages.map((m) => (
            <div key={m.id} className={`message-bubble message-${m.role}`}>
              <div className="message-header">
                <strong>{m.role === 'user' ? 'You' : 'Sahara'}</strong>
                <span className="message-time">
                  {new Date(m.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
              </div>
              <div className="message-body">{m.content}</div>
              {m.role === 'assistant' && (
                <button
                  className="btn-speak-again"
                  onClick={() => speakText(m.content)}
                  title="Read aloud again"
                >
                  🔊 Listen again
                </button>
              )}
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        {/* Quick topic buttons for easy interaction without typing */}
        <div className="quick-prompts-bar">
          <button onClick={() => handleSend('Tell me a gentle story about morning in a sunny garden.')}>
            📖 Tell me a story
          </button>
          <button onClick={() => handleSend('What medications or reminders do I have today?')}>
            💊 Today's reminders
          </button>
          <button onClick={() => handleSend("I want to do my daily check-in now.")}>
            ☀️ Daily check-in
          </button>
          <button onClick={() => handleSend('Remind me to drink a fresh glass of water.')}>
            💧 Drink water
          </button>
        </div>
      </div>

      {/* Voice and input controls */}
      <div className="chat-input-bar">
        <button
          className={`mic-button ${voiceState === 'listening' ? 'mic-active' : ''}`}
          onClick={toggleListening}
          aria-label={voiceState === 'listening' ? 'Stop listening' : 'Start speaking'}
        >
          <span className="mic-icon">{voiceState === 'listening' ? '⏹' : '🎤'}</span>
          <span className="mic-label">{voiceState === 'listening' ? 'Tap to Stop' : 'Tap to Speak'}</span>
        </button>

        <form
          className="chat-form"
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
        >
          <input
            type="text"
            className="chat-text-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your message here or use the mic..."
          />
          <button type="submit" className="btn-send-message" disabled={!input.trim()}>
            Send ➜
          </button>
        </form>
      </div>
    </div>
  );
}
