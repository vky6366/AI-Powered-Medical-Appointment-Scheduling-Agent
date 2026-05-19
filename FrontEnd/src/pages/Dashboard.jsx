import { useState, useEffect, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { getMyAppointments, cancelAppointment, sendChat, getDoctors } from '../api/services';
import AppointmentsTab from '../components/AppointmentsTab';
import ScheduleTab from '../components/ScheduleTab';
import ChatTab from '../components/ChatTab';
import ProfileTab from '../components/ProfileTab';

const NAV = [
  { id: 'appointments', label: 'Appointments', icon: '📅' },
  { id: 'schedule', label: 'Schedule', icon: '➕' },
  { id: 'chat', label: 'AI Assistant', icon: '🤖' },
  { id: 'profile', label: 'Profile', icon: '👤' },
];

export default function Dashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('appointments');
  const [appointments, setAppointments] = useState([]);
  const [aptsLoading, setAptsLoading] = useState(true);
  const [aptsError, setAptsError] = useState('');

  const fetchAppointments = async () => {
    setAptsLoading(true); setAptsError('');
    try {
      const { data } = await getMyAppointments();
      setAppointments(Array.isArray(data) ? data : data.appointments || []);
    } catch (e) {
      setAptsError('Could not load appointments.');
    } finally { setAptsLoading(false); }
  };

  useEffect(() => { fetchAppointments(); }, []);

  const handleLogout = () => { logout(); navigate('/login'); };

  const sidebarStyle = (active) => ({
    display: 'flex', alignItems: 'center', gap: 12,
    padding: '0.875rem 1.25rem', borderRadius: 12, cursor: 'pointer',
    fontWeight: 600, fontSize: '0.9rem', border: 'none', width: '100%', textAlign: 'left',
    transition: 'all 0.2s',
    background: active ? 'linear-gradient(135deg, #0ea5e9, #6366f1)' : 'rgba(255,255,255,0.03)',
    color: active ? 'white' : 'rgba(255,255,255,0.6)',
    boxShadow: active ? '0 4px 16px rgba(14,165,233,0.3)' : 'none',
    border: active ? 'none' : '1px solid rgba(255,255,255,0.06)',
  });

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #0f172a 0%, #0c1e35 100%)',
      display: 'flex', flexDirection: 'column',
    }}>
      {/* Header */}
      <header style={{
        background: 'rgba(255,255,255,0.03)',
        borderBottom: '1px solid rgba(255,255,255,0.07)',
        backdropFilter: 'blur(12px)',
        padding: '0 2rem', height: 64,
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        position: 'sticky', top: 0, zIndex: 100,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{
            width: 36, height: 36, borderRadius: 10,
            background: 'linear-gradient(135deg,#0ea5e9,#6366f1)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: 'white', fontWeight: 900, fontSize: 18,
          }}>+</div>
          <span style={{ color: 'white', fontWeight: 700, fontSize: '1.1rem' }}>
            AIHealth<span style={{ color: '#38bdf8' }}>Care</span>
          </span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          {user?.profile_picture && (
            <img src={user.profile_picture} alt="avatar"
              style={{ width: 36, height: 36, borderRadius: '50%', border: '2px solid rgba(56,189,248,0.5)' }} />
          )}
          <span style={{ color: 'rgba(255,255,255,0.7)', fontSize: '0.875rem' }}>{user?.name}</span>
          <button onClick={handleLogout} style={{
            padding: '0.4rem 1rem', borderRadius: 8,
            background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)',
            color: '#f87171', fontSize: '0.8rem', cursor: 'pointer', fontWeight: 600,
          }}>Sign Out</button>
        </div>
      </header>

      {/* Body */}
      <div style={{ display: 'flex', flex: 1, maxWidth: 1200, margin: '0 auto', width: '100%', padding: '2rem', gap: '1.5rem' }}>
        {/* Sidebar */}
        <nav style={{ width: 220, flexShrink: 0, display: 'flex', flexDirection: 'column', gap: 8 }}>
          {NAV.map(({ id, label, icon }) => (
            <button key={id} onClick={() => setActiveTab(id)} style={sidebarStyle(activeTab === id)}>
              <span style={{ fontSize: 18 }}>{icon}</span>
              {label}
            </button>
          ))}
        </nav>

        {/* Content */}
        <main style={{ flex: 1, minWidth: 0 }}>
          {activeTab === 'appointments' && (
            <AppointmentsTab
              appointments={appointments} loading={aptsLoading}
              error={aptsError} onRefresh={fetchAppointments}
              onCancel={async (id) => {
                await cancelAppointment(id);
                fetchAppointments();
              }}
              onSchedule={() => setActiveTab('schedule')}
            />
          )}
          {activeTab === 'schedule' && (
            <ScheduleTab onBooked={() => { setActiveTab('appointments'); fetchAppointments(); }} />
          )}
          {activeTab === 'chat' && <ChatTab />}
          {activeTab === 'profile' && <ProfileTab user={user} />}
        </main>
      </div>
    </div>
  );
}
