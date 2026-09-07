import React, { useState, useEffect } from 'react';
import { LogIn, LogOut, User } from 'lucide-react';

export const AuthButton: React.FC = () => {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('admin123');
  const [showLogin, setShowLogin] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      const response = await fetch('/api/v1/auth/me', {
        credentials: 'include',
      });
      if (response.ok) {
        const data = await response.json();
        setIsAuthenticated(true);
        setUsername(data.username || 'User');
      } else {
        setIsAuthenticated(false);
      }
    } catch (error) {
      setIsAuthenticated(false);
    }
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      // EXACTLY match the successful curl request format
      const formData = new URLSearchParams();
      formData.append('username', username);
      formData.append('password', password);
      // 'stay_signed_in' is not strictly required by the backend form as long as it handles the default,
      // but let's include it to be safe.
      formData.append('stay_signed_in', 'false');

      const response = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: formData.toString(),
        credentials: 'include',
      });

      console.log('Login response status:', response.status);

      if (response.ok || response.status === 303) {
        setIsAuthenticated(true);
        setShowLogin(false);
        setPassword('');
        setError(null);
        window.location.reload();
      } else {
        const text = await response.text();
        console.error('Login failed:', response.status, text);
        setError(`Login failed (${response.status}). Please check credentials.`);
      }
    } catch (error) {
      console.error('Login error:', error);
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    try {
      await fetch('/api/v1/auth/logout', {
        method: 'POST',
        credentials: 'include',
      });
      setIsAuthenticated(false);
      window.location.reload();
    } catch (error) {
      console.error('Logout error:', error);
    }
  };

  if (isAuthenticated === null) return null;

  if (isAuthenticated) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <span style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)' }}>
          <User size={16} style={{ verticalAlign: 'middle', marginRight: '4px' }} />
          {username}
        </span>
        <button
          onClick={handleLogout}
          style={{
            padding: '6px 14px',
            borderRadius: '6px',
            background: 'var(--color-bg-tertiary)',
            border: '1px solid var(--glass-border)',
            color: 'var(--color-text-secondary)',
            cursor: 'pointer',
            fontSize: '0.8rem',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
          }}
        >
          <LogOut size={14} /> Logout
        </button>
      </div>
    );
  }

  return (
    <>
      <button
        onClick={() => setShowLogin(true)}
        style={{
          padding: '8px 16px',
          borderRadius: '8px',
          background: 'var(--color-gas)',
          border: 'none',
          color: 'var(--color-bg-primary)',
          cursor: 'pointer',
          fontWeight: 600,
          fontSize: '0.85rem',
        }}
      >
        <LogIn size={14} style={{ marginRight: '6px' }} /> Login
      </button>

      {showLogin && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          background: 'rgba(0,0,0,0.8)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          zIndex: 9999,
        }}>
          <form 
            onSubmit={handleLogin}
            style={{
              background: 'var(--color-bg-primary)',
              padding: '2rem',
              borderRadius: '16px',
              border: '1px solid var(--glass-border)',
              width: '360px',
            }}
          >
            <h2 style={{ marginBottom: '1rem', color: 'var(--color-text-primary)' }}>Login to Studio</h2>
            {error && <div style={{ color: 'var(--color-danger)', marginBottom: '1rem', fontSize: '0.8rem' }}>{error}</div>}
            <input
              type="text"
              placeholder="Username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              style={{ width: '100%', padding: '10px', marginBottom: '10px', background: 'var(--color-bg-secondary)', border: '1px solid var(--glass-border)', borderRadius: '8px', color: 'var(--color-text-primary)' }}
            />
            <input
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              style={{ width: '100%', padding: '10px', marginBottom: '16px', background: 'var(--color-bg-secondary)', border: '1px solid var(--glass-border)', borderRadius: '8px', color: 'var(--color-text-primary)' }}
            />
            <div style={{ display: 'flex', gap: '8px' }}>
              <button type="submit" disabled={loading} style={{ flex: 1, padding: '10px', background: 'var(--color-gas)', border: 'none', borderRadius: '8px', color: 'var(--color-bg-primary)', fontWeight: 600, cursor: 'pointer' }}>
                {loading ? 'Logging in...' : 'Login'}
              </button>
              <button type="button" onClick={() => setShowLogin(false)} style={{ padding: '10px 20px', background: 'var(--color-bg-secondary)', border: '1px solid var(--glass-border)', borderRadius: '8px', color: 'var(--color-text-secondary)', cursor: 'pointer' }}>
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}
    </>
  );
};
