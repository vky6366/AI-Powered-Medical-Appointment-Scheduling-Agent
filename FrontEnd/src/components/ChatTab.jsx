import { useState, useEffect, useRef } from 'react';
import { sendChat } from '../api/services';
import { useAuth } from '../context/AuthContext';

const CARD = { background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 16 };

export default function ChatTab() {
  const { user } = useAuth();
  const [messages, setMessages] = useState([
    { role: 'bot', text: `Hello ${user?.name?.split(' ')[0] || 'there'}! 👋 I'm your AI health assistant. Tell me your symptoms and I'll help schedule the right appointment for you.` }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [threadId] = useState(() => `user-chat-${Date.now()}`);
  const [availableSlots, setAvailableSlots] = useState([]);
  const [nextStep, setNextStep] = useState(null);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const send = async (msgText, slotId = null) => {
    if (!msgText.trim() && !slotId) return;
    const userMsg = msgText.trim() || `Booking slot ${slotId}`;
    setMessages(prev => [...prev, { role: 'user', text: userMsg }]);
    setInput('');
    setLoading(true);
    setAvailableSlots([]);
    try {
      const { data } = await sendChat(userMsg, threadId, slotId);
      setNextStep(data.next_step);
      setMessages(prev => [...prev, { role: 'bot', text: data.message, data: data.data }]);
      if (data.available_slots?.length) setAvailableSlots(data.available_slots);
      if (data.appointment_id) {
        setMessages(prev => [...prev, {
          role: 'system',
          text: `✅ Appointment confirmed! ID: ${data.appointment_id}`,
        }]);
      }
    } catch (err) {
      setMessages(prev => [...prev, { role: 'bot', text: '⚠️ Sorry, something went wrong. Please try again.' }]);
    } finally { setLoading(false); }
  };

  const handleSubmit = (e) => { e.preventDefault(); send(input); };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 160px)' }}>
      <div style={{ marginBottom: '1rem' }}>
        <h2 style={{ color: 'white', fontSize: '1.5rem', fontWeight: 700, margin: 0 }}>🤖 AI Health Assistant</h2>
        <p style={{ color: 'rgba(255,255,255,0.4)', fontSize: '0.875rem', marginTop: 4 }}>
          Describe your symptoms and I'll help book the right appointment
        </p>
      </div>

      {/* Messages */}
      <div style={{
        ...CARD, flex: 1, overflowY: 'auto', padding: '1.25rem',
        display: 'flex', flexDirection: 'column', gap: 12, marginBottom: 12,
      }}>
        {messages.map((msg, i) => (
          <div key={i} style={{ display: 'flex', justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start' }}>
            {msg.role === 'system' ? (
              <div style={{
                width: '100%', textAlign: 'center', padding: '0.5rem 1rem',
                background: 'rgba(74,222,128,0.1)', border: '1px solid rgba(74,222,128,0.2)',
                borderRadius: 10, color: '#4ade80', fontSize: '0.875rem', fontWeight: 600,
              }}>{msg.text}</div>
            ) : (
              <div style={{
                maxWidth: '75%', padding: '0.75rem 1rem', borderRadius: 16,
                borderBottomRightRadius: msg.role === 'user' ? 4 : 16,
                borderBottomLeftRadius: msg.role === 'bot' ? 4 : 16,
                background: msg.role === 'user'
                  ? 'linear-gradient(135deg, #0ea5e9, #6366f1)'
                  : 'rgba(255,255,255,0.07)',
                color: 'white', fontSize: '0.9rem', lineHeight: 1.5,
              }}>
                {msg.text}
              </div>
            )}
          </div>
        ))}

        {/* Slot picker */}
        {availableSlots.length > 0 && (
          <div style={{
            background: 'rgba(14,165,233,0.08)', border: '1px solid rgba(14,165,233,0.2)',
            borderRadius: 12, padding: '1rem',
          }}>
            <p style={{ color: '#38bdf8', fontSize: '0.875rem', fontWeight: 600, marginBottom: 10 }}>
              Available Slots — pick one:
            </p>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
              {availableSlots.map((slot) => (
                <button key={slot.slot_id} onClick={() => send(`I'll take slot ${slot.slot_id}`, slot.slot_id)} style={{
                  padding: '0.5rem 0.875rem', borderRadius: 8,
                  background: 'rgba(14,165,233,0.15)', border: '1px solid rgba(14,165,233,0.4)',
                  color: '#38bdf8', cursor: 'pointer', fontSize: '0.8rem', fontWeight: 600,
                }}>
                  {new Date(slot.start).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })}
                  {' · '}
                  {new Date(slot.start).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })}
                </button>
              ))}
            </div>
          </div>
        )}

        {loading && (
          <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
            <div style={{
              padding: '0.75rem 1rem', borderRadius: 16, borderBottomLeftRadius: 4,
              background: 'rgba(255,255,255,0.07)',
            }}>
              <div style={{ display: 'flex', gap: 4 }}>
                {[0, 1, 2].map(i => (
                  <div key={i} style={{
                    width: 8, height: 8, borderRadius: '50%', background: '#38bdf8',
                    animation: `bounce 1s ease ${i * 0.15}s infinite`,
                  }} />
                ))}
              </div>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} style={{ display: 'flex', gap: 10 }}>
        <input
          value={input} onChange={(e) => setInput(e.target.value)}
          placeholder="Describe your symptoms, e.g. 'I have chest pain and shortness of breath'..."
          style={{
            flex: 1, padding: '0.875rem 1.25rem', borderRadius: 12,
            background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.12)',
            color: 'white', fontSize: '0.9rem', outline: 'none',
          }}
        />
        <button type="submit" disabled={loading || !input.trim()} style={{
          padding: '0.875rem 1.5rem', borderRadius: 12,
          background: 'linear-gradient(135deg,#0ea5e9,#6366f1)',
          border: 'none', color: 'white', fontWeight: 700, cursor: 'pointer',
          opacity: loading || !input.trim() ? 0.5 : 1,
        }}>Send</button>
      </form>

      <style>{`
        @keyframes bounce { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-6px)} }
      `}</style>
    </div>
  );
}
