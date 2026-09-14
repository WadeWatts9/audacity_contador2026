import React, { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useGame } from '../../context/GameContext';
import { KeyRound, Users, ShieldAlert } from 'lucide-react';

export const Login: React.FC = () => {
  const { login } = useAuth();
  const { gameCode, setGameCode } = useGame();

  const [inputGameCode, setInputGameCode] = useState(gameCode);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const codeToUse = inputGameCode.trim().toUpperCase() || undefined;
      const user = await login(username.trim(), password, codeToUse);
      if (user.game_code) {
        setGameCode(user.game_code);
      } else if (codeToUse) {
        setGameCode(codeToUse);
      }
    } catch (err: any) {
      setError(err.message || 'Error al iniciar sesión.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '440px', margin: '40px auto' }}>
      <div className="workspace" style={{ boxShadow: 'var(--shadow-lg)' }}>
        <div style={{ textAlign: 'center', marginBottom: '24px' }}>
          <h2 style={{ fontFamily: 'Georgia, serif', fontSize: '28px', marginBottom: '6px' }}>
            Ingreso a la Partida
          </h2>
          <p style={{ color: '#405c50', fontSize: '14px' }}>
            Ingresá con tus credenciales de equipo o como docente/banco.
          </p>
        </div>

        {error && (
          <div
            style={{
            background: '#fde8e8',
            border: '2px solid #db3448',
            padding: '12px',
            borderRadius: '4px',
            marginBottom: '18px',
            color: '#9b1c1c',
            fontSize: '14px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
          }}
          >
            <ShieldAlert size={18} />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div>
            <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '6px', fontSize: '14px' }}>
              Usuario:
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              placeholder="admin_docente o gallo_contador..."
              style={{
                width: '100%',
                padding: '10px 12px',
                border: '2px solid var(--ink)',
                borderRadius: '4px',
                fontSize: '15px',
                background: '#fffdf5',
              }}
            />
          </div>

          <div>
            <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '6px', fontSize: '14px' }}>
              Contraseña:
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              placeholder="Contraseña (ej. gallo123 o contraseña docente)"
              style={{
                width: '100%',
                padding: '10px 12px',
                border: '2px solid var(--ink)',
                borderRadius: '4px',
                fontSize: '15px',
                background: '#fffdf5',
              }}
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="btn btn-primary"
            style={{ width: '100%', justifyContent: 'center', padding: '12px', marginTop: '8px' }}
          >
            <KeyRound size={18} />
            <span>{loading ? 'Ingresando...' : 'Iniciar Sesión'}</span>
          </button>
        </form>

        <div style={{ marginTop: '20px', borderTop: '1px solid #c0d0c4', paddingTop: '14px', fontSize: '12px', color: '#556b62', textAlign: 'center' }}>
          Dinero ficticio expresado en TDL · Sin cuentas externas · 100% Red Local
        </div>
      </div>
    </div>
  );
};
