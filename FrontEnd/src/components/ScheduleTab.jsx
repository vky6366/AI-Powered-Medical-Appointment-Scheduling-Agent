import { useState, useEffect } from 'react';
import { getDoctors, getAvailableSlots, bookAppointment } from '../api/services';
import { useAuth } from '../context/AuthContext';

const CARD = { background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 16, padding: '1.5rem' };
const INPUT_STYLE = {
  width: '100%', padding: '0.75rem 1rem', borderRadius: 10,
  background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.12)',
  color: 'white', fontSize: '0.875rem', outline: 'none', boxSizing: 'border-box',
};
const LABEL_STYLE = { color: 'rgba(255,255,255,0.6)', fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: 6 };

export default function ScheduleTab({ onBooked }) {
  const { user } = useAuth();
  const [doctors, setDoctors] = useState([]);
  const [form, setForm] = useState({ doctor: '', date: '', problem: '', problem_description: '', returning_patient: false });
  const [slots, setSlots] = useState([]);
  const [selectedSlot, setSelectedSlot] = useState(null);
  const [slotsLoading, setSlotsLoading] = useState(false);
  const [booking, setBooking] = useState(false);
  const [success, setSuccess] = useState(null);
  const [error, setError] = useState('');
  const [step, setStep] = useState(1); // 1=doctor+date, 2=slot+reason, 3=confirm

  useEffect(() => {
    getDoctors().then(({ data }) => setDoctors(data.doctors || [])).catch(() => {});
  }, []);

  const fetchSlots = async () => {
    if (!form.doctor || !form.date) return;
    setSlotsLoading(true); setSlots([]); setSelectedSlot(null);
    try {
      const { data } = await getAvailableSlots(form.doctor, form.date);
      setSlots(data.slots || []);
      setStep(2);
    } catch { setError('Could not fetch slots.'); }
    finally { setSlotsLoading(false); }
  };

  const handleBook = async () => {
    if (!selectedSlot) return;
    setBooking(true); setError('');
    try {
      const payload = {
        name: user?.name, email: user?.email,
        doctor: form.doctor, date: form.date,
        start: selectedSlot.start, end: selectedSlot.end,
        problem: form.problem, problem_description: form.problem_description,
        returning_patient: form.returning_patient,
      };
      const { data } = await bookAppointment(payload);
      setSuccess(data.booking_id);
      setStep(3);
    } catch (e) {
      setError(e.response?.data?.detail || e.response?.data?.error || 'Booking failed.');
    } finally { setBooking(false); }
  };

  if (step === 3 && success) return (
    <div style={{ ...CARD, textAlign: 'center', padding: '4rem 2rem' }}>
      <div style={{ fontSize: 64, marginBottom: 16 }}>✅</div>
      <h2 style={{ color: 'white', fontWeight: 700, fontSize: '1.5rem', marginBottom: 8 }}>Appointment Booked!</h2>
      <p style={{ color: 'rgba(255,255,255,0.5)', marginBottom: 8 }}>Booking ID: <span style={{ color: '#38bdf8' }}>{success}</span></p>
      <p style={{ color: 'rgba(255,255,255,0.4)', fontSize: '0.875rem', marginBottom: 24 }}>A confirmation email has been sent to {user?.email}</p>
      <button onClick={onBooked} style={{
        padding: '0.75rem 2rem', borderRadius: 12,
        background: 'linear-gradient(135deg,#0ea5e9,#6366f1)',
        border: 'none', color: 'white', fontWeight: 700, cursor: 'pointer',
      }}>View My Appointments</button>
    </div>
  );

  return (
    <div>
      <div style={{ marginBottom: '1.5rem' }}>
        <h2 style={{ color: 'white', fontSize: '1.5rem', fontWeight: 700, margin: 0 }}>Schedule Appointment</h2>
        <p style={{ color: 'rgba(255,255,255,0.4)', fontSize: '0.875rem', marginTop: 4 }}>Book directly or use the AI Assistant</p>
      </div>

      {/* Step indicators */}
      <div style={{ display: 'flex', gap: 8, marginBottom: '1.5rem' }}>
        {['Select Doctor & Date', 'Pick a Slot', 'Confirm'].map((label, i) => (
          <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8, flex: 1 }}>
            <div style={{
              width: 28, height: 28, borderRadius: '50%', flexShrink: 0,
              background: step > i + 1 ? '#4ade80' : step === i + 1 ? 'linear-gradient(135deg,#0ea5e9,#6366f1)' : 'rgba(255,255,255,0.1)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              color: 'white', fontSize: '0.75rem', fontWeight: 700,
            }}>{step > i + 1 ? '✓' : i + 1}</div>
            <span style={{ color: step === i + 1 ? 'white' : 'rgba(255,255,255,0.35)', fontSize: '0.8rem', fontWeight: step === i + 1 ? 600 : 400 }}>{label}</span>
            {i < 2 && <div style={{ flex: 1, height: 1, background: 'rgba(255,255,255,0.1)' }} />}
          </div>
        ))}
      </div>

      {error && (
        <div style={{ marginBottom: 16, padding: '0.75rem 1rem', background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: 10, color: '#f87171', fontSize: '0.875rem' }}>
          ⚠️ {error}
        </div>
      )}

      {/* Step 1 */}
      {step >= 1 && (
        <div style={{ ...CARD, marginBottom: 16 }}>
          <h3 style={{ color: 'white', fontWeight: 600, marginBottom: '1.25rem', fontSize: '1rem' }}>Step 1: Select Doctor & Date</h3>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <div>
              <label style={LABEL_STYLE}>Doctor</label>
              <select value={form.doctor} onChange={e => { setForm({ ...form, doctor: e.target.value }); setStep(1); setSlots([]); }}
                style={{ ...INPUT_STYLE, colorScheme: 'dark' }}>
                <option value="">Select a doctor...</option>
                {doctors.map(d => (
                  <option key={d.id} value={d.name}>{d.name} — {d.specialty}</option>
                ))}
              </select>
            </div>
            <div>
              <label style={LABEL_STYLE}>Preferred Date</label>
              <input type="date" min={new Date().toISOString().split('T')[0]}
                value={form.date} onChange={e => { setForm({ ...form, date: e.target.value }); setStep(1); setSlots([]); }}
                style={{ ...INPUT_STYLE, colorScheme: 'dark' }} />
            </div>
          </div>
          <button onClick={fetchSlots} disabled={!form.doctor || !form.date || slotsLoading}
            style={{
              marginTop: '1rem', padding: '0.65rem 1.5rem', borderRadius: 10,
              background: !form.doctor || !form.date ? 'rgba(255,255,255,0.1)' : 'linear-gradient(135deg,#0ea5e9,#6366f1)',
              border: 'none', color: 'white', fontWeight: 600, cursor: !form.doctor || !form.date ? 'not-allowed' : 'pointer',
              fontSize: '0.875rem',
            }}>
            {slotsLoading ? 'Checking availability...' : 'Check Available Slots →'}
          </button>
        </div>
      )}

      {/* Step 2 */}
      {step >= 2 && (
        <div style={{ ...CARD, marginBottom: 16 }}>
          <h3 style={{ color: 'white', fontWeight: 600, marginBottom: '1.25rem', fontSize: '1rem' }}>Step 2: Choose a Slot & Describe Your Visit</h3>

          {slots.length === 0 ? (
            <p style={{ color: 'rgba(255,255,255,0.4)', fontSize: '0.875rem' }}>No available slots on this date. Please try another date.</p>
          ) : (
            <div>
              <label style={LABEL_STYLE}>Available Slots</label>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: '1.25rem' }}>
                {slots.map((slot, i) => (
                  <button key={i} onClick={() => setSelectedSlot(slot)}
                    style={{
                      padding: '0.5rem 0.875rem', borderRadius: 8, cursor: 'pointer',
                      fontWeight: 600, fontSize: '0.8rem', border: 'none',
                      background: selectedSlot?.start === slot.start ? 'linear-gradient(135deg,#0ea5e9,#6366f1)' : 'rgba(255,255,255,0.08)',
                      color: 'white',
                      boxShadow: selectedSlot?.start === slot.start ? '0 4px 12px rgba(14,165,233,0.3)' : 'none',
                    }}>
                    {slot.start} – {slot.end}
                  </button>
                ))}
              </div>
            </div>
          )}

          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <div>
              <label style={LABEL_STYLE}>Reason for Visit</label>
              <input type="text" placeholder="e.g. Chest pain, routine checkup"
                value={form.problem} onChange={e => setForm({ ...form, problem: e.target.value })}
                style={INPUT_STYLE} />
            </div>
            <div>
              <label style={LABEL_STYLE}>Additional Details</label>
              <textarea rows={3} placeholder="Describe your symptoms or concerns..."
                value={form.problem_description} onChange={e => setForm({ ...form, problem_description: e.target.value })}
                style={{ ...INPUT_STYLE, resize: 'none' }} />
            </div>
            <label style={{ ...LABEL_STYLE, display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}>
              <input type="checkbox" checked={form.returning_patient}
                onChange={e => setForm({ ...form, returning_patient: e.target.checked })}
                style={{ width: 16, height: 16, accentColor: '#0ea5e9' }} />
              <span>I am a returning patient</span>
            </label>
          </div>

          <button onClick={handleBook} disabled={!selectedSlot || booking}
            style={{
              marginTop: '1.25rem', padding: '0.75rem 2rem', borderRadius: 12,
              background: !selectedSlot ? 'rgba(255,255,255,0.1)' : 'linear-gradient(135deg,#0ea5e9,#6366f1)',
              border: 'none', color: 'white', fontWeight: 700, cursor: !selectedSlot ? 'not-allowed' : 'pointer',
              boxShadow: selectedSlot ? '0 4px 16px rgba(14,165,233,0.3)' : 'none',
            }}>
            {booking ? 'Booking...' : '✓ Confirm Appointment'}
          </button>
        </div>
      )}
    </div>
  );
}
