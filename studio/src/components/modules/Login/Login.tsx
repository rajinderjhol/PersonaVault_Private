import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../../store/authStore';
import { Lock, User } from 'lucide-react';

const Login: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const navigate = useNavigate();
  const { login, isAuthenticating, error } = useAuthStore();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await login(username, password);
    // After login, check auth status from the store
    // Since login is async, we can check the state if we had a way to wait for it or just check it here.
    // For now, let's rely on authStore's state.
  };

  // Effect to redirect once authenticated
  const { isAuthenticated } = useAuthStore();
  React.useEffect(() => {
    if (isAuthenticated) {
      navigate('/');
    }
  }, [isAuthenticated, navigate]);

  return (
    <div style={{ 
      display: 'flex',
      justifyContent: 'center', 
      alignItems: 'center', 
      height: '100vh', 
      backgroundColor: 'var(--color-bg-primary)' 
    }}>
      <form onSubmit={handleSubmit} style={{ 
        backgroundColor: 'var(--color-bg-secondary)', 
        padding: '40px', 
        borderRadius: '16px', 
        border: '1px solid var(--glass-border)',
        width: '100%',
        maxWidth: '400px'
      }}>
        <h2 style={{ marginBottom: '24px', color: 'var(--color-text-primary)', textAlign: 'center' }}>PersonaVault Login</h2>
        
        {error && <div style={{ color: 'var(--color-error)', marginBottom: '16px', fontSize: '0.9rem' }}>{error}</div>}

        <div style={{ marginBottom: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px', color: 'var(--color-text-secondary)' }}>
            <User size={16} /> Username
          </div>
          <input 
            type="text" 
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            style={{ width: '100%', padding: '10px', borderRadius: '8px', border: '1px solid var(--glass-border)', background: 'var(--color-bg-primary)', color: 'white' }}
          />
        </div>

        <div style={{ marginBottom: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px', color: 'var(--color-text-secondary)' }}>
            <Lock size={16} /> Password
          </div>
          <input 
            type="password" 
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            style={{ width: '100%', padding: '10px', borderRadius: '8px', border: '1px solid var(--glass-border)', background: 'var(--color-bg-primary)', color: 'white' }}
          />
        </div>

        <button 
          type="submit" 
          disabled={isAuthenticating}
          style={{ 
            width: '100%', 
            padding: '12px', 
            borderRadius: '8px', 
            border: 'none', 
            backgroundColor: 'var(--color-gas)', 
            color: 'black', 
            fontWeight: 600,
            cursor: 'pointer' 
          }}
        >
          {isAuthenticating ? 'Logging in...' : 'Login'}
        </button>
      </form>
    </div>
  );
};

export default Login;
