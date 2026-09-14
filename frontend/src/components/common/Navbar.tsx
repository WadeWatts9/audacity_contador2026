import React from 'react';
import { useAuth } from '../../context/AuthContext';
import { useGame } from '../../context/GameContext';
import { LogOut, Monitor, RefreshCw } from 'lucide-react';

export const Navbar: React.FC<{
  onToggleProjection?: () => void;
  isProjection?: boolean;
}> = ({ onToggleProjection, isProjection }) => {
  const { user, logout } = useAuth();
  const { gameCode, summary, refreshGame, loading } = useGame();

  return (
    <header className="audacity-header">
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <h1 className="brand">AUDACITY</h1>
        {gameCode && (
          <span
            className="badge"
            style={{
              backgroundColor: '#fffdf5',
              fontSize: '15px',
              padding: '6px 12px',
              letterSpacing: '0.05em',
            }}
          >
            SALA: <strong>{gameCode}</strong>
          </span>
        )}
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
        {summary?.server_time && (
          <span style={{ fontSize: '13px', color: '#172d29', fontWeight: 600 }}>
            🕒 {summary.server_time}
          </span>
        )}

        {gameCode && (
          <button
            onClick={() => refreshGame()}
            disabled={loading}
            className="btn"
            style={{ padding: '6px 10px', fontSize: '13px' }}
            title="Sincronizar"
          >
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          </button>
        )}

        {onToggleProjection && (
          <button
            onClick={onToggleProjection}
            className={`btn ${isProjection ? 'btn-gold' : ''}`}
            style={{ padding: '6px 12px', fontSize: '13px' }}
            title="Modo Proyector para el aula"
          >
            <Monitor size={15} />
            <span>{isProjection ? 'Salir Proyector' : 'Modo Proyector'}</span>
          </button>
        )}

        {user && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span
              className="token-circle"
              style={{
                backgroundColor: user.token_color || '#fff',
                width: '32px',
                height: '32px',
                fontSize: '17px',
              }}
              title={user.display_name}
            >
              {user.token_symbol || '👤'}
            </span>
            <span style={{ fontWeight: 'bold', fontSize: '14px' }}>
              {user.display_name}
            </span>
            <button
              onClick={logout}
              className="btn btn-red"
              style={{ padding: '6px 10px', fontSize: '13px' }}
              title="Cerrar sesión"
            >
              <LogOut size={14} />
            </button>
          </div>
        )}
      </div>
    </header>
  );
};
