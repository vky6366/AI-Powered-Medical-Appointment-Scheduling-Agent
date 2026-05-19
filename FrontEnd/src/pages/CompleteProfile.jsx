import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { completeProfile } from '../api/services';

export default function CompleteProfile() {
  const { user, markProfileComplete, logout } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({
    phone: '', dob: '',
    insurance_carrier: '', insurance_member_id: '', insurance_group: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.phone.trim()) { setError('Phone number is required.'); return; }
    setLoading(true); setError('');
    try {
      await completeProfile(form);
      markProfileComplete();
      navigate('/dashboard', { replace: true });
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save profile. Please try again.');
    } finally { setLoading(false); }
  };

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #0f172a 0%, #1e3a5f 50%, #0f172a 100%)',
      display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '2rem',
    }}>
      <div style={{
        width: '100%', maxWidth: 520,
        background: 'rgba(255,255,255,0.05)',
        backdropFilter: 'blur(20px)',
        border: '1px solid rgba(255,255,255,0.1)',
        borderRadius: 24, padding: '2.5rem',
        boxShadow: '0 25px 60px rgba(0,0,0,0.4)',
      }}>
        {/* Avatar + greeting */}
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          {user?.profile_picture ? (
            <img src={user.profile_picture} alt="avatar"
              style={{ width: 72, height: 72, borderRadius: '50%', border: '3px solid #38bdf8', marginBottom: 12 }} />
          ) : (
            <div style={{
              width: 72, height: 72, borderRadius: '50%',
              background: 'linear-gradient(135deg,#0ea5e9,#6366f1)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 28, fontWeight: 700, color: 'white', margin: '0 auto 12px',
            }}>
              {user?.name?.[0] || '?'}
            </div>
          )}
          <h2 style={{ color: 'white', fontSize: '1.5rem', fontWeight: 700, margin: 0 }}>
            Welcome, {user?.name?.split(' ')[0]}! 👋
          </h2>
          <p style={{ color: 'rgba(255,255,255,0.5)', marginTop: 6, fontSize: '0.875rem' }}>
            Complete your profile to get started
          </p>
        </div>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {/* Phone */}
          <div>
            <label style={{ color: 'rgba(255,255,255,0.7)', fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: 6 }}>
              📞 Phone Number <span style={{ color: '#f87171' }}>*</span>
            </label>
            <input name="phone" type="tel" required value={form.phone} onChange={handleChange}
              placeholder="+91 98765 43210"
              style={{
                width: '100%', padding: '0.75rem 1rem', borderRadius: 10,
                background: 'rgba(255,255,255,0.07)', border: '1px solid rgba(255,255,255,0.15)',
                color: 'white', fontSize: '0.9rem', outline: 'none', boxSizing: 'border-box',
              }} />
          </div>

          {/* DOB */}
          <div>
            <label style={{ color: 'rgba(255,255,255,0.7)', fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: 6 }}>
              🎂 Date of Birth <span style={{ color: 'rgba(255,255,255,0.3)', fontWeight: 400 }}>(optional)</span>
            </label>
            <input name="dob" type="date" value={form.dob} onChange={handleChange}
              style={{
                width: '100%', padding: '0.75rem 1rem', borderRadius: 10,
                background: 'rgba(255,255,255,0.07)', border: '1px solid rgba(255,255,255,0.15)',
                color: 'white', fontSize: '0.9rem', outline: 'none', boxSizing: 'border-box',
                colorScheme: 'dark',
              }} />
          </div>

          {/* Insurance Section */}
          <div style={{
            background: 'rgba(255,255,255,0.03)',
            border: '1px solid rgba(255,255,255,0.08)',
            borderRadius: 12, padding: '1rem',
          }}>
            <p style={{ color: 'rgba(255,255,255,0.5)', fontSize: '0.8rem', fontWeight: 600, marginBottom: 12 }}>
              🏥 Insurance Information (optional)
            </p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {[
                { name: 'insurance_carrier', label: 'Insurance Carrier', placeholder: 'e.g. BlueCross' },
                { name: 'insurance_member_id', label: 'Member ID', placeholder: 'Your member ID' },
                { name: 'insurance_group', label: 'Group Number', placeholder: 'Your group number' },
              ].map(({ name, label, placeholder }) => (
                <div key={name}>
                  <label style={{ color: 'rgba(255,255,255,0.5)', fontSize: '0.75rem', display: 'block', marginBottom: 4 }}>{label}</label>
                  <input name={name} type="text" value={form[name]} onChange={handleChange}
                    placeholder={placeholder}
                    style={{
                      width: '100%', padding: '0.6rem 0.875rem', borderRadius: 8,
                      background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)',
                      color: 'white', fontSize: '0.85rem', outline: 'none', boxSizing: 'border-box',
                    }} />
                </div>
              ))}
            </div>
          </div>

          {error && (
            <div style={{
              padding: '0.75rem 1rem', background: 'rgba(239,68,68,0.15)',
              border: '1px solid rgba(239,68,68,0.3)', borderRadius: 10,
              color: '#fca5a5', fontSize: '0.875rem',
            }}>⚠️ {error}</div>
          )}

          <button type="submit" disabled={loading}
            style={{
              padding: '0.875rem', borderRadius: 12,
              background: loading ? 'rgba(14,165,233,0.5)' : 'linear-gradient(135deg, #0ea5e9, #6366f1)',
              color: 'white', fontWeight: 700, fontSize: '1rem', border: 'none',
              cursor: loading ? 'not-allowed' : 'pointer',
              boxShadow: '0 4px 20px rgba(14,165,233,0.3)',
              transition: 'all 0.2s',
            }}>
            {loading ? 'Saving...' : 'Complete Profile & Get Started →'}
          </button>

          <button type="button" onClick={logout}
            style={{
              background: 'none', border: 'none', color: 'rgba(255,255,255,0.3)',
              fontSize: '0.8rem', cursor: 'pointer', textAlign: 'center',
            }}>
            Sign out and use a different account
          </button>
        </form>
      </div>
    </div>
  );
}
