import React, { useState } from 'react';
import { useAuthStore } from '../../../store/authStore';

const Login: React.FC = () => {
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('admin123');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      // Use form-urlencoded format (same as backend Form dependencies)
      const formData = new URLSearchParams();
      formData.append('username', username);
      formData.append('password', password);

      console.log('🔑 Sending login request...');
      
      const response = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: formData.toString(),
        credentials: 'include',
      });

      console.log('📡 Login response status:', response.status);

      // Backend returns 303 on success
      if (response.status === 303 || response.status === 302 || response.ok) {
        console.log('✅ Login successful!');
        // Reload to refresh auth state
        window.location.href = '/studio';
        return;
      } else {
        const text = await response.text();
        setError(`Login failed (${response.status})`);
        console.error('Login error:', text);
      }
    } catch (err) {
      setError('Network error. Make sure the backend is running.');
      console.error('Login error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      minHeight: '100vh',
      background: '#0a0e1a',
    }}>
      <div style={{
        background: '#141a2e',
        padding: '2rem',
        borderRadius: '16px',
        border: '1px solid rgba(77,150,255,0.15)',
        width: '380px',
        maxWidth: '90%',
        boxShadow: '0 24px 64px rgba(0,0,0,0.6)',
      }}>
        <h1 style={{ color: '#e8edf5', fontSize: '1.5rem', marginBottom: '0.5rem' }}>
          🧠 PersonaVault Studio
        </h1>
        <p style={{ color: '#6a7fa0', marginBottom: '2rem', fontSize: '0.9rem' }}>
          Login to access the Sovereign AI Studio
        </p>

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ color: '#a0b4d0', fontSize: '0.85rem', display: 'block', marginBottom: '0.25rem' }}>
              Username
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              style={{
                width: '100%',
                padding: '10px 14px',
                background: '#0a0e1a',
                border: '1px solid rgba(77,150,255,0.15)',
                borderRadius: '8px',
                color: '#e8edf5',
                fontSize: '1rem',
                fontFamily: 'inherit',
                outline: 'none',
              }}
              placeholder="admin"
              required
            />
          </div>

          <div style={{ marginBottom: '1.5rem' }}>
            <label style={{ color: '#a0b4d0', fontSize: '0.85rem', display: 'block', marginBottom: '0.25rem' }}>
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              style={{
                width: '100%',
                padding: '10px 14px',
                background: '#0a0e1a',
                border: '1px solid rgba(77,150,255,0.15)',
                borderRadius: '8px',
                color: '#e8edf5',
                fontSize: '1rem',
                fontFamily: 'inherit',
                outline: 'none',
              }}
              placeholder="••••••••"
              required
            />
          </div>

          {error && (
            <div style={{
              padding: '10px 14px',
              marginBottom: '1rem',
              background: 'rgba(255, 107, 107, 0.1)',
              borderRadius: '8px',
              color: '#ff6b6b',
              fontSize: '0.9rem',
              border: '1px solid rgba(255, 107, 107, 0.2)',
            }}>
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            style={{
              width: '100%',
              padding: '12px',
              background: '#00f2ff',
              border: 'none',
              borderRadius: '8px',
              color: '#0a0e1a',
              fontWeight: 600,
              fontSize: '1rem',
              cursor: loading ? 'default' : 'pointer',
              fontFamily: 'inherit',
              opacity: loading ? 0.6 : 1,
            }}
          >
            {loading ? 'Logging in...' : 'Login'}
          </button>

          <div style={{ 
            marginTop: '1rem', 
            textAlign: 'center',
            fontSize: '0.8rem',
            color: '#6a7fa0',
          }}>
            Default: admin / admin123
          </div>
        </form>
      </div>
    </div>
  );
};

export default Login;
