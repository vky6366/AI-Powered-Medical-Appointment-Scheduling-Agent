import { useState } from 'react';

const CARD = {
  background: 'rgba(255,255,255,0.04)',
  border: '1px solid rgba(255,255,255,0.08)',
  borderRadius: 16, padding: '1.5rem',
};

export default function AppointmentsTab({ appointments, loading, error, onRefresh, onCancel, onSchedule }) {
  if (loading) return (
    <div style={{ textAlign: 'center', paddingTop: '4rem' }}>
      <div style={{
        width: 40, height: 40, border: '3px solid rgba(255,255,255,0.1)',
        borderTopColor: '#38bdf8', borderRadius: '50%',
        animation: 'spin 0.8s linear infinite', margin: '0 auto 1rem',
      }} />
      <p style={{ color: 'rgba(255,255,255,0.4)' }}>Loading appointments...</p>
      <style>{`@keyframes spin{to{transform:rotate(360deg)}}`}</style>
    </div>
  );

  if (error) return (
    <div style={{ ...CARD, borderColor: 'rgba(239,68,68,0.3)', textAlign: 'center', padding: '3rem' }}>
      <p style={{ color: '#f87171', marginBottom: 16 }}>⚠️ {error}</p>
      <button onClick={onRefresh} style={{
        padding: '0.5rem 1.5rem', borderRadius: 10,
        background: 'rgba(239,68,68,0.15)', border: '1px solid rgba(239,68,68,0.3)',
        color: '#f87171', cursor: 'pointer',
      }}>Retry</button>
    </div>
  );

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <div>
          <h2 style={{ color: 'white', fontSize: '1.5rem', fontWeight: 700, margin: 0 }}>My Appointments</h2>
          <p style={{ color: 'rgba(255,255,255,0.4)', fontSize: '0.875rem', marginTop: 4 }}>
            {appointments.length} appointment{appointments.length !== 1 ? 's' : ''} found
          </p>
        </div>
        <button onClick={onSchedule} style={{
          padding: '0.6rem 1.25rem', borderRadius: 10,
          background: 'linear-gradient(135deg,#0ea5e9,#6366f1)',
          border: 'none', color: 'white', fontWeight: 600, cursor: 'pointer',
          fontSize: '0.875rem', boxShadow: '0 4px 12px rgba(14,165,233,0.3)',
        }}>+ Schedule New</button>
      </div>

      {appointments.length === 0 ? (
        <div style={{ ...CARD, textAlign: 'center', padding: '4rem 2rem' }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>📅</div>
          <h3 style={{ color: 'white', fontWeight: 600, marginBottom: 8 }}>No appointments yet</h3>
          <p style={{ color: 'rgba(255,255,255,0.4)', marginBottom: 24, fontSize: '0.875rem' }}>
            Use the AI assistant or schedule directly to book your first appointment
          </p>
          <button onClick={onSchedule} style={{
            padding: '0.75rem 2rem', borderRadius: 12,
            background: 'linear-gradient(135deg,#0ea5e9,#6366f1)',
            border: 'none', color: 'white', fontWeight: 600, cursor: 'pointer',
          }}>Book Appointment</button>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {appointments.map((apt) => (
            <AptCard key={apt.id || apt.appointment_id} apt={apt} onCancel={onCancel} />
          ))}
        </div>
      )}
    </div>
  );
}

function AptCard({ apt, onCancel }) {
  const [cancelling, setCancelling] = useState(false);
  const id = apt.id || apt.appointment_id;
  const status = (apt.status || 'scheduled').toLowerCase();
  const statusColor = {
    confirmed: '#4ade80', scheduled: '#4ade80',
    pending: '#fbbf24', cancelled: '#f87171', completed: '#818cf8',
  }[status] || '#94a3b8';

  const handleCancel = async () => {
    if (!confirm('Cancel this appointment?')) return;
    setCancelling(true);
    try { await onCancel(id); } catch { alert('Failed to cancel.'); }
    setCancelling(false);
  };

  const dateStr = apt.appointment_date
    ? new Date(apt.appointment_date).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })
    : apt.start_time ? new Date(apt.start_time).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }) : '—';

  const timeStr = apt.appointment_start || (apt.start_time ? new Date(apt.start_time).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }) : '—');

  return (
    <div style={{
      ...CARD,
      borderLeft: `3px solid ${statusColor}`,
      display: 'flex', justifyContent: 'space-between', alignItems: 'center',
      flexWrap: 'wrap', gap: 12,
    }}>
      <div style={{ flex: 1 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6, flexWrap: 'wrap' }}>
          <h4 style={{ color: 'white', fontWeight: 700, margin: 0, fontSize: '1rem' }}>
            {apt.doctor || apt.doctor_name || 'Doctor'}
          </h4>
          <span style={{
            padding: '2px 10px', borderRadius: 20, fontSize: '0.7rem', fontWeight: 700,
            background: `${statusColor}20`, color: statusColor, textTransform: 'capitalize',
          }}>{status}</span>
        </div>
        {apt.problem && <p style={{ color: 'rgba(255,255,255,0.5)', margin: '0 0 8px', fontSize: '0.85rem' }}>💬 {apt.problem}</p>}
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
          <span style={{ color: '#38bdf8', fontSize: '0.8rem' }}>📅 {dateStr}</span>
          <span style={{ color: 'rgba(255,255,255,0.4)', fontSize: '0.8rem' }}>🕐 {timeStr}</span>
          {apt.appointment_end && <span style={{ color: 'rgba(255,255,255,0.4)', fontSize: '0.8rem' }}>→ {apt.appointment_end}</span>}
        </div>
      </div>
      {['scheduled', 'confirmed', 'pending'].includes(status) && (
        <button onClick={handleCancel} disabled={cancelling} style={{
          padding: '0.4rem 1rem', borderRadius: 8,
          background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)',
          color: '#f87171', cursor: cancelling ? 'not-allowed' : 'pointer',
          fontSize: '0.8rem', fontWeight: 600, whiteSpace: 'nowrap',
        }}>{cancelling ? 'Cancelling...' : 'Cancel'}</button>
      )}
    </div>
  );
}
