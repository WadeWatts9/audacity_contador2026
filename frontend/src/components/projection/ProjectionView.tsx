import React from 'react';
import { useGame } from '../../context/GameContext';
import { ShieldCheck } from 'lucide-react';

export const ProjectionView: React.FC = () => {
  const { summary } = useGame();

  return (
    <div style={{ padding: '10px 0' }}>
      {/* Banner de Partida Finalizada en Proyección */}
      {summary?.game.status === 'finalizada' && (
        <div
          style={{
            background: '#fef3c7',
            border: '3px solid #d97706',
            borderRadius: '8px',
            padding: '16px',
            textAlign: 'center',
            marginBottom: '20px',
            color: '#92400e',
          }}
        >
          <div style={{ font: '900 clamp(24px, 3.5vw, 36px) Georgia, serif' }}>🏁 PARTIDA FINALIZADA 🏁</div>
          <div style={{ fontSize: '18px', marginTop: '4px', fontWeight: 600 }}>
            ¡El podio oficial ha quedado fijado! Felicitaciones al equipo ganador.
          </div>
        </div>
      )}

      {/* Top Banner de Proyección */}
      <div
        className="workspace"
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          background: '#fffdf5',
          border: '3px solid var(--ink)',
          marginBottom: '24px',
        }}
      >
        <div>
          <span style={{ fontSize: '15px', fontWeight: 'bold', color: '#405c50', letterSpacing: '0.05em' }}>
            RONDA {summary?.game.current_turn_number || 1} · EQUIPO EN TURNO
          </span>
          <div style={{ font: '900 36px Georgia, serif', color: 'var(--red)', marginTop: '4px' }}>
            {summary?.active_team_name || 'Esperando inicio'}
          </div>
        </div>

        <div style={{ textAlign: 'right' }}>
          <span style={{ fontSize: '14px', fontWeight: 'bold', color: '#405c50' }}>FONDOS DEL BANCO CENTRAL</span>
          <div style={{ font: '700 30px Georgia, serif', color: 'var(--ink)' }}>
            TDL {((summary?.bank_balance || 0) / 100).toLocaleString('es-UY', { minimumFractionDigits: 2 })}
          </div>
        </div>
      </div>

      {/* Tabla Gigante de Ranking */}
      <div className="workspace" style={{ border: '3px solid var(--ink)' }}>
        <h2 style={{ font: '900 clamp(24px, 3.5vw, 36px) Georgia, serif', textAlign: 'center', marginBottom: '20px' }}>
          POSICIONES DE LA PARTIDA
        </h2>

        <table className="table-audacity" style={{ fontSize: 'clamp(16px, 2vw, 22px)' }}>
          <thead>
            <tr>
              <th style={{ textAlign: 'center', width: '90px' }}>Puesto</th>
              <th>Equipo</th>
              <th style={{ textAlign: 'right' }}>Disponible</th>
              <th style={{ textAlign: 'right' }}>Reservado</th>
              <th style={{ textAlign: 'right' }}>Total Nominal</th>
              <th style={{ textAlign: 'center' }}>Estado</th>
            </tr>
          </thead>
          <tbody>
            {summary?.ranking.map((team) => (
              <tr key={team.account_id} style={{ background: team.rank === 1 ? '#fdf8e6' : undefined }}>
                <td style={{ textAlign: 'center', fontWeight: '900', font: '700 28px Georgia, serif' }}>
                  #{team.rank}
                </td>
                <td>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                    <span
                      className="token-circle"
                      style={{
                        backgroundColor: team.token_color,
                        width: '46px',
                        height: '46px',
                        fontSize: '24px',
                      }}
                    >
                      {team.token_symbol}
                    </span>
                    <strong>{team.team_name}</strong>
                  </div>
                </td>
                <td style={{ textAlign: 'right', fontWeight: 'bold' }}>
                  {(team.balance_available / 100).toLocaleString('es-UY', { minimumFractionDigits: 2 })}
                </td>
                <td style={{ textAlign: 'right', color: '#556b62' }}>
                  {(team.balance_reserved / 100).toLocaleString('es-UY', { minimumFractionDigits: 2 })}
                </td>
                <td style={{ textAlign: 'right', font: '700 26px Georgia, serif', color: 'var(--green)' }}>
                  {(team.balance_total / 100).toLocaleString('es-UY', { minimumFractionDigits: 2 })} TDL
                </td>
                <td style={{ textAlign: 'center', fontSize: '15px' }}>
                  {team.lost_turns > 0 ? (
                    <span className="badge" style={{ background: '#fde8e8', color: '#9b1c1c' }}>
                      Pierde {team.lost_turns} turno
                    </span>
                  ) : team.has_insurance_e11 ? (
                    <span className="badge" style={{ background: '#def7ec', color: '#03543f' }}>
                      <ShieldCheck size={14} style={{ display: 'inline' }} /> Con Seguro
                    </span>
                  ) : (
                    'Activo'
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
