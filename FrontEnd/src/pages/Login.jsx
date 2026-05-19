import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { googleAuth } from '../api/services';

const GOOGLE_CLIENT_ID = 'your_google_client_id'; // Replace with your actual Google Client ID if needed

export default function Login() {
  const { login, token, profileComplete } = useAuth();
  const navigate = useNavigate();
  const btnRef = useRef(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [scriptLoaded, setScriptLoaded] = useState(false);

  // Redirect if already logged in
  useEffect(() => {
    if (token) {
      navigate(profileComplete ? '/dashboard' : '/complete-profile', { replace: true });
    }
  }, [token, profileComplete, navigate]);

  // Load Google GIS script dynamically and initialize
  useEffect(() => {
    const initializeGoogleSignIn = () => {
      if (!window.google) return;
      try {
        window.google.accounts.id.initialize({
          client_id: GOOGLE_CLIENT_ID,
          callback: handleGoogleResponse,
        });
        window.google.accounts.id.renderButton(btnRef.current, {
          theme: 'outline',
          size: 'large',
          width: 370,
          text: 'signin_with',
          shape: 'rectangular',
        });
      } catch (err) {
        console.error('Failed to initialize Google Sign-In:', err);
      }
    };

    if (window.google) {
      setScriptLoaded(true);
      initializeGoogleSignIn();
    } else {
      const script = document.createElement('script');
      script.src = 'https://accounts.google.com/gsi/client';
      script.async = true;
      script.defer = true;
      script.onload = () => {
        setScriptLoaded(true);
        initializeGoogleSignIn();
      };
      document.body.appendChild(script);
    }
  }, [scriptLoaded]);

  const handleGoogleResponse = async (response) => {
    setLoading(true);
    setError('');
    try {
      const { data } = await googleAuth(response.credential);
      login(data.access_token, data.user, data.profile_complete);
      navigate(data.profile_complete ? '/dashboard' : '/complete-profile', { replace: true });
    } catch (err) {
      setError(err.response?.data?.detail || 'Google login failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Skip Login for Local Dev & Testing (Bypass Auth with Demo Mode)
  const handleDemoLogin = () => {
    const demoToken = 'demo-jwt-token-xyz';
    const demoUser = {
      id: 1,
      name: 'John Doe',
      email: 'john.doe@example.com',
      profile_picture: null,
      last_login: new Date().toISOString(),
    };
    login(demoToken, demoUser, true);
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
            {/* Real Google Auth Container */}
            <div ref={btnRef} style={{ width: '100%', minHeight: 40 }} />

            {/* Quick Demo Mode Bypass (Highly Requested for Dev/Testing) */}
            <button
              onClick={handleDemoLogin}
              style={{
                width: '100%',
                padding: '0.75rem',
                borderRadius: 4,
                background: 'linear-gradient(135deg, #0ea5e9, #6366f1)',
                border: 'none',
                color: 'white',
                fontWeight: 700,
                cursor: 'pointer',
                fontSize: '0.9rem',
                boxShadow: '0 4px 14px rgba(14,165,233,0.3)',
                transition: 'transform 0.1s ease, filter 0.2s',
              }}
              onMouseOver={(e) => e.currentTarget.style.filter = 'brightness(1.1)'}
              onMouseOut={(e) => e.currentTarget.style.filter = 'none'}
            >
              🚀 Enter in Demo / Dev Mode
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
