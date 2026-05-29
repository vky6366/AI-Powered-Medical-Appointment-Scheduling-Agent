import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { googleAuth } from '../api/services';
import { auth, googleProvider } from '../firebase';
import { signInWithPopup } from 'firebase/auth';

export default function Login() {
  const { login, token, profileComplete } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  // Redirect if already logged in
  useEffect(() => {
    if (token) {
      navigate(profileComplete ? '/dashboard' : '/complete-profile', { replace: true });
    }
  }, [token, profileComplete, navigate]);

  const handleGoogleLogin = async () => {
    setLoading(true);
    setError('');
    try {
      // Sign in with Firebase popup
      const result = await signInWithPopup(auth, googleProvider);
      // Retrieve the Firebase ID Token
      const firebaseIdToken = await result.user.getIdToken();
      // Send token to the backend
      const { data } = await googleAuth(firebaseIdToken);
      login(data.access_token, data.user, data.profile_complete);
      navigate(data.profile_complete ? '/dashboard' : '/complete-profile', { replace: true });
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || err.message || 'Google login failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #0f172a 0%, #1e3a5f 50%, #0f172a 100%)',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '1rem',
      position: 'relative',
      overflow: 'hidden',
    }}>
      {/* Animated blobs */}
      <div style={{
        position: 'absolute', width: 400, height: 400,
        borderRadius: '50%', top: '-100px', right: '-100px',
        background: 'radial-gradient(circle, rgba(14,165,233,0.15) 0%, transparent 70%)',
        pointerEvents: 'none',
      }} />
      <div style={{
        position: 'absolute', width: 300, height: 300,
        borderRadius: '50%', bottom: '-50px', left: '-50px',
        background: 'radial-gradient(circle, rgba(99,102,241,0.12) 0%, transparent 70%)',
        pointerEvents: 'none',
      }} />

      {/* Card */}
      <div style={{
        width: '100%', maxWidth: 420,
        background: 'rgba(255,255,255,0.05)',
        backdropFilter: 'blur(20px)',
        border: '1px solid rgba(255,255,255,0.1)',
        borderRadius: 24,
        padding: '2.5rem',
        boxShadow: '0 25px 60px rgba(0,0,0,0.4)',
        boxSizing: 'border-box',
      }}>
        {/* Logo */}
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <div style={{
            width: 64, height: 64,
            background: 'linear-gradient(135deg, #0ea5e9, #6366f1)',
            borderRadius: 18,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            margin: '0 auto 1rem',
            fontSize: 28, color: 'white', fontWeight: 900,
            boxShadow: '0 8px 24px rgba(14,165,233,0.4)',
          }}>+</div>
          <h1 style={{ color: 'white', fontSize: '1.75rem', fontWeight: 700, margin: 0 }}>
            AIHealth<span style={{ color: '#38bdf8' }}>Care</span>
          </h1>
          <p style={{ color: 'rgba(255,255,255,0.5)', marginTop: '0.5rem', fontSize: '0.9rem' }}>
            Your AI-powered medical assistant
          </p>
        </div>

        {/* Features */}
        <div style={{ marginBottom: '2rem', display: 'flex', flexDirection: 'column', gap: 10 }}>
          {[
            { icon: '🤖', text: 'AI-driven appointment scheduling' },
            { icon: '🩺', text: 'Symptom-based doctor matching' },
            { icon: '📅', text: 'Instant slot booking & reminders' },
          ].map(({ icon, text }) => (
            <div key={text} style={{
              display: 'flex', alignItems: 'center', gap: 10,
              color: 'rgba(255,255,255,0.7)', fontSize: '0.875rem',
            }}>
              <span style={{ fontSize: 18 }}>{icon}</span>
              <span>{text}</span>
            </div>
          ))}
        </div>

        {/* Google Button */}
        {loading ? (
          <div style={{ textAlign: 'center', padding: '1rem' }}>
            <div className="spinner" style={{
              width: 32, height: 32, border: '3px solid rgba(255,255,255,0.2)',
              borderTopColor: '#38bdf8', borderRadius: '50%',
              animation: 'spin 0.8s linear infinite', margin: '0 auto',
            }} />
            <p style={{ color: 'rgba(255,255,255,0.6)', marginTop: 8, fontSize: '0.875rem' }}>Signing you in...</p>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12, width: '100%' }}>
            {/* Custom Google Auth Button */}
            <button
              onClick={handleGoogleLogin}
              style={{
                width: '100%',
                padding: '0.75rem',
                borderRadius: 4,
                background: 'white',
                border: 'none',
                color: '#1e293b',
                fontWeight: 700,
                cursor: 'pointer',
                fontSize: '0.9rem',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '10px',
                boxShadow: '0 4px 14px rgba(255,255,255,0.1)',
                transition: 'transform 0.1s ease, filter 0.2s',
              }}
              onMouseOver={(e) => e.currentTarget.style.filter = 'brightness(0.95)'}
              onMouseOut={(e) => e.currentTarget.style.filter = 'none'}
            >
              <svg width="18" height="18" viewBox="0 0 24 24">
                <path fill="#4285F4" d="M23.745 12.27c0-.7-.06-1.4-.19-2.07H12v3.92h6.69c-.29 1.5-1.14 2.78-2.4 3.63v3.02h3.88c2.27-2.09 3.57-5.17 3.57-8.5z"/>
                <path fill="#34A853" d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.88-3.02c-1.08.72-2.45 1.16-4.05 1.16-3.11 0-5.74-2.11-6.68-4.96H1.21v3.11C3.18 21.88 7.31 24 12 24z"/>
                <path fill="#FBBC05" d="M5.32 14.27c-.24-.72-.38-1.49-.38-2.27s.14-1.55.38-2.27V6.62H1.21C.44 8.24 0 10.06 0 12s.44 3.76 1.21 5.38l4.11-3.11z"/>
                <path fill="#EA4335" d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.31 0 3.18 2.12 1.21 5.38l4.11 3.11c.94-2.85 3.57-4.96 6.68-4.96z"/>
              </svg>
              Sign in with Google
            </button>
          </div>
        )}

        {error && (
          <div style={{
            marginTop: '1rem',
            padding: '0.75rem 1rem',
            background: 'rgba(239,68,68,0.15)',
            border: '1px solid rgba(239,68,68,0.3)',
            borderRadius: 10,
            color: '#fca5a5',
            fontSize: '0.875rem',
          }}>
            ⚠️ {error}
          </div>
        )}

        <p style={{
          marginTop: '1.5rem', textAlign: 'center',
          color: 'rgba(255,255,255,0.3)', fontSize: '0.75rem',
        }}>
          By signing in, you agree to our Terms of Service and Privacy Policy
        </p>
      </div>

      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
      `}</style>
    </div>
  );
}
