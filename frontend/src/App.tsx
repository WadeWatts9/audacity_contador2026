import React, { useState } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { GameProvider, useGame } from './context/GameContext';
import { Navbar } from './components/common/Navbar';
import { Login } from './components/auth/Login';
import { TeacherDashboard } from './components/teacher/TeacherDashboard';
import { TeamDashboard } from './components/team/TeamDashboard';
import { ProjectionView } from './components/projection/ProjectionView';
import { Bell } from 'lucide-react';
import './styles/audacity.css';

const AppContent: React.FC = () => {
  const { user, loading } = useAuth();
  const { notification, setNotification } = useGame();
  const [isProjection, setIsProjection] = useState(false);

  if (loading) {
    return (
      <main className="audacity-board" style={{ textAlign: 'center', padding: '60px' }}>
        <h2 style={{ fontFamily: 'Georgia, serif' }}>Cargando Audacity...</h2>
      </main>
    );
  }

  return (
    <main className="audacity-board">
      {/* Pista superior de casillas de colores */}
      <div className="track" aria-hidden="true">
        <span></span><span></span><span></span><span></span><span></span>
        <span></span><span></span><span></span><span></span><span></span>
      </div>

      <Navbar
        isProjection={isProjection}
        onToggleProjection={user ? () => setIsProjection(!isProjection) : undefined}
      />

      {/* Notificación en vivo */}
      {notification && (
        <div
          style={{
            background: '#fffdf5',
            border: '2px solid var(--gold)',
            padding: '10px 16px',
            marginBottom: '16px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            boxShadow: 'var(--shadow)',
            fontWeight: 600,
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Bell size={16} color="var(--gold)" />
            <span>{notification}</span>
          </div>
          <button
            onClick={() => setNotification(null)}
            style={{ background: 'none', border: 'none', cursor: 'pointer', fontWeight: 'bold' }}
          >
            ✕
          </button>
        </div>
      )}

      {!user ? (
        <Login />
      ) : isProjection ? (
        <ProjectionView />
      ) : user.role === 'admin_docente' ? (
        <TeacherDashboard />
      ) : (
        <TeamDashboard />
      )}

      <footer
        style={{
          marginTop: '36px',
          padding: '18px 24px',
          background: '#0a1118',
          border: '1px solid #1e293b',
          borderRadius: '8px',
          textAlign: 'center',
          color: '#e2e8f0',
          fontSize: '13px',
          lineHeight: '1.8',
          boxShadow: '0 4px 12px rgba(0,0,0,0.25)',
        }}
      >
        <div style={{ fontWeight: 500 }}>
          © 2026 Lic. Prof. Alan Canto - taller de Economía para Jóvenes. Todos los derechos reservados.
        </div>
        <div style={{ marginTop: '4px', color: '#94a3b8', fontSize: '13px' }}>
          Desarrollado por{' '}
          <a
            href="https://www.instagram.com/alancanto.insta"
            target="_blank"
            rel="noopener noreferrer"
            style={{
              color: '#ef4444',
              fontWeight: 700,
              textDecoration: 'none',
              letterSpacing: '0.02em',
              transition: 'color 0.2s ease',
            }}
          >
            Alan Canto ACDEV
          </a>
        </div>
      </footer>
    </main>
  );
};

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <GameProvider>
        <AppContent />
      </GameProvider>
    </AuthProvider>
  );
};

export default App;
