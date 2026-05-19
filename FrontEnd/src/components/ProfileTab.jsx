const CARD = { background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 16, padding: '1.5rem' };

export default function ProfileTab({ user }) {
  const initials = user?.name ? user.name.split(' ').map(n => n[0]).join('').toUpperCase() : '?';

  return (
    <div>
      <h2 style={{ color: 'white', fontSize: '1.5rem', fontWeight: 700, marginBottom: '1.5rem' }}>My Profile</h2>

      {/* Avatar Card */}
      <div style={{
        ...CARD,
        display: 'flex', alignItems: 'center', gap: '1.5rem',
        marginBottom: 16,
        background: 'linear-gradient(135deg, rgba(14,165,233,0.1), rgba(99,102,241,0.1))',
        borderColor: 'rgba(14,165,233,0.2)',
      }}>
        {user?.profile_picture ? (
          <img src={user.profile_picture} alt="avatar"
            style={{ width: 80, height: 80, borderRadius: '50%', border: '3px solid rgba(56,189,248,0.5)' }} />
        ) : (
          <div style={{
            width: 80, height: 80, borderRadius: '50%',
            background: 'linear-gradient(135deg,#0ea5e9,#6366f1)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: '1.75rem', fontWeight: 700, color: 'white', flexShrink: 0,
          }}>{initials}</div>
        )}
        <div>
          <h3 style={{ color: 'white', fontWeight: 700, fontSize: '1.25rem', margin: 0 }}>{user?.name || 'Patient'}</h3>
          <p style={{ color: 'rgba(255,255,255,0.5)', fontSize: '0.875rem', marginTop: 4 }}>{user?.email}</p>
          <span style={{
            display: 'inline-block', marginTop: 8,
            padding: '3px 12px', borderRadius: 20, fontSize: '0.7rem', fontWeight: 700,
            background: 'rgba(74,222,128,0.15)', color: '#4ade80', border: '1px solid rgba(74,222,128,0.3)',
          }}>● Active Patient</span>
        </div>
      </div>

      {/* Info Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 16 }}>
        {[
          { label: '👤 Full Name', value: user?.name },
          { label: '📧 Email', value: user?.email },
          { label: '🆔 User ID', value: user?.id ? `#${user.id}` : '—' },
          { label: '🕐 Last Login', value: user?.last_login ? new Date(user.last_login).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' }) : '—' },
        ].map(({ label, value }) => (
          <div key={label} style={{ ...CARD, padding: '1rem 1.25rem' }}>
            <p style={{ color: 'rgba(255,255,255,0.4)', fontSize: '0.75rem', fontWeight: 600, margin: 0, marginBottom: 4 }}>{label}</p>
            <p style={{ color: 'white', fontWeight: 600, margin: 0, fontSize: '0.9rem', wordBreak: 'break-all' }}>{value || '—'}</p>
          </div>
        ))}
      </div>

      {/* Auth Info */}
      <div style={{ ...CARD }}>
        <h4 style={{ color: 'rgba(255,255,255,0.6)', fontSize: '0.8rem', fontWeight: 700, marginBottom: 12, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Authentication</h4>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
            <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
            <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
            <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z" fill="#FBBC05"/>
            <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
          </svg>
          <span style={{ color: 'rgba(255,255,255,0.7)', fontSize: '0.875rem' }}>Signed in with Google</span>
          <span style={{
            marginLeft: 'auto', padding: '2px 10px', borderRadius: 20, fontSize: '0.7rem', fontWeight: 700,
            background: 'rgba(74,222,128,0.15)', color: '#4ade80',
          }}>Active</span>
        </div>
      </div>
    </div>
  );
}
