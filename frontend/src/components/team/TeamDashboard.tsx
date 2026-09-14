import React, { useState, useEffect } from 'react';
import { useGame } from '../../context/GameContext';
import { useAuth } from '../../context/AuthContext';
import { api } from '../../api/client';
import { MyTeamStatus, Card } from '../../types';
import { ArrowRightLeft, ShieldCheck, Clock, Wallet, History, Send, FileText } from 'lucide-react';

export const TeamDashboard: React.FC = () => {
  const { gameCode, summary, pDeck, eDeck, countPAvailable, countEAvailable, refreshGame } = useGame();
  const { user } = useAuth();

  const [status, setStatus] = useState<MyTeamStatus | null>(null);
  const [loading, setLoading] = useState(true);

  // Transfer modal
  const [showTransferModal, setShowTransferModal] = useState(false);
  const [destAccountId, setDestAccountId] = useState<number | ''>('');
  const [transferAmountTDL, setTransferAmountTDL] = useState<number>(50);
  const [transferReason, setTransferReason] = useState<string>('');
  const [transferring, setTransferring] = useState(false);

  // Active card inspection modal
  const [selectedCard, setSelectedCard] = useState<Card | null>(null);

  const fetchStatus = async () => {
    try {
      const data = await api.getMyTeamStatus();
      setStatus(data);
    } catch (err) {
      console.error('Error fetching team status:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    const timer = setInterval(fetchStatus, 3000);
    return () => clearInterval(timer);
  }, []);

  const handleDrawCard = async (type: 'P' | 'E', code?: string) => {
    if (!gameCode) return;
    try {
      const card = await api.drawCard(gameCode, type, code);
      setSelectedCard(card);
      fetchStatus();
      refreshGame();
    } catch (err: any) {
      alert(err.message || 'No se pudo tomar la tarjeta.');
    }
  };

  const handleTransferSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!destAccountId) return;
    setTransferring(true);
    try {
      const amountCents = Math.round(transferAmountTDL * 100);
      const res = await api.teamTransfer({
        destination_account_id: Number(destAccountId),
        amount_cents: amountCents,
        reason: transferReason,
      });
      alert(res.message);
      setShowTransferModal(false);
      setTransferReason('');
      fetchStatus();
      refreshGame();
    } catch (err: any) {
      alert('Error en transferencia: ' + err.message);
    } finally {
      setTransferring(false);
    }
  };

  if (loading && !status) {
    return (
      <div className="workspace" style={{ textAlign: 'center', padding: '40px' }}>
        Cargando estado del equipo...
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Header del Equipo y Turno */}
      <div className="workspace" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <span
            className="token-circle"
            style={{
              backgroundColor: status?.color || '#fff',
              width: '54px',
              height: '54px',
              fontSize: '30px',
            }}
          >
            {status?.symbol || '★'}
          </span>
          <div>
            <h2 style={{ font: '700 28px Georgia, serif', margin: 0 }}>{status?.team_name}</h2>
            <div style={{ display: 'flex', gap: '8px', marginTop: '4px', flexWrap: 'wrap' }}>
              {status?.is_my_turn ? (
                <span className="badge" style={{ background: 'var(--green)', color: 'white', fontSize: '13px' }}>
                  🎯 ¡ES EL TURNO DE TU EQUIPO!
                </span>
              ) : (
                <span className="badge" style={{ background: '#f5fbf7', color: '#405c50' }}>
                  Esperando turno... (Ronda {status?.current_round})
                </span>
              )}

              {status?.lost_turns && status.lost_turns > 0 ? (
                <span className="badge" style={{ background: '#fde8e8', color: '#9b1c1c' }}>
                  ⏳ {status.lost_turns} turno(s) perdido(s)
                </span>
              ) : null}

              {status?.has_insurance_e11 && (
                <span className="badge" style={{ background: '#def7ec', color: '#03543f' }}>
                  <ShieldCheck size={13} style={{ display: 'inline', verticalAlign: 'middle' }} /> Seguro E11 Activo
                </span>
              )}
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap' }}>
          <a
            href="/guia_estudiante_audacity.pdf"
            target="_blank"
            rel="noopener noreferrer"
            className="btn"
            style={{ textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '6px', padding: '10px 14px' }}
            title="Abrir o descargar la Guía de Uso Oficial en PDF para estudiantes"
          >
            <FileText size={16} />
            <span>Guía de Uso (PDF)</span>
          </a>

          <button
            onClick={() => setShowTransferModal(true)}
            className="btn btn-primary"
            style={{ padding: '10px 18px', fontSize: '15px' }}
          >
            <Send size={16} />
            <span>Transferir / Pagar</span>
          </button>
        </div>
      </div>

      {/* Tarjetas de Saldos Patrimoniales */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
        <div className="workspace" style={{ borderLeft: '8px solid var(--green)', background: '#fffdf5' }}>
          <div style={{ fontSize: '13px', fontWeight: 'bold', color: '#405c50', textTransform: 'uppercase' }}>
            Saldo Disponible (Gasto / Transferencias)
          </div>
          <div style={{ font: '700 32px Georgia, serif', color: 'var(--green)', marginTop: '4px' }}>
            TDL {((status?.balance_available || 0) / 100).toLocaleString('es-UY', { minimumFractionDigits: 2 })}
          </div>
        </div>

        <div className="workspace" style={{ borderLeft: '8px solid var(--blue)', background: '#fffdf5' }}>
          <div style={{ fontSize: '13px', fontWeight: 'bold', color: '#405c50', textTransform: 'uppercase' }}>
            Saldo Reservado (Ahorro / Plazo Fijo)
          </div>
          <div style={{ font: '700 32px Georgia, serif', color: 'var(--blue)', marginTop: '4px' }}>
            TDL {((status?.balance_reserved || 0) / 100).toLocaleString('es-UY', { minimumFractionDigits: 2 })}
          </div>
        </div>

        <div className="workspace" style={{ borderLeft: '8px solid var(--ink)', background: '#fffdf5' }}>
          <div style={{ fontSize: '13px', fontWeight: 'bold', color: '#405c50', textTransform: 'uppercase' }}>
            Saldo Total Nominal
          </div>
          <div style={{ font: '700 32px Georgia, serif', color: 'var(--ink)', marginTop: '4px' }}>
            TDL {((status?.balance_total || 0) / 100).toLocaleString('es-UY', { minimumFractionDigits: 2 })}
          </div>
        </div>
      </div>

      {/* Mazos P y E para elegir si la casilla lo indica */}
      {/* Aviso de Partida Finalizada */}
      {summary?.game.status === 'finalizada' && (
        <div
          style={{
            background: '#fef3c7',
            border: '2px solid #d97706',
            borderRadius: '6px',
            padding: '16px 20px',
            color: '#92400e',
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
          }}
        >
          <span style={{ fontSize: '24px' }}>🏁</span>
          <div>
            <strong style={{ fontSize: '16px', display: 'block' }}>¡PARTIDA FINALIZADA!</strong>
            <span style={{ fontSize: '14px' }}>El docente ha cerrado el juego. El tablero y las posiciones finales han quedado fijados.</span>
          </div>
        </div>
      )}

      {/* Tarjetas Jugadas (Preguntas y Retos) */}
      {(() => {
        const usedPCards = pDeck.filter((c) => c.status === 'resuelta_usada');
        const usedECards = eDeck.filter((c) => c.status === 'resuelta_usada');

        return (
          <div className="workspace">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px', flexWrap: 'wrap', gap: '10px' }}>
              <h3 style={{ fontFamily: 'Georgia, serif', fontSize: '20px', margin: 0 }}>
                Tarjetas Jugadas (Preguntas y Retos)
              </h3>
              <span style={{ fontSize: '13px', color: '#556b62', background: '#f5fbf7', padding: '4px 10px', borderRadius: '4px', border: '1px solid #c0d0c4' }}>
                ℹ️ Los retos y preguntas no son visibles en el mazo. Se hacen visibles aquí una vez seleccionados y marcados como no disponibles por el docente.
              </span>
            </div>

            {/* Sección Preguntas (P) */}
            <div style={{ marginBottom: '24px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                <strong style={{ color: 'var(--blue)', fontSize: '15px' }}>
                  📘 Preguntas Jugadas: {usedPCards.length} visibles ({countPAvailable} en el mazo)
                </strong>
              </div>

              {usedPCards.length === 0 ? (
                <div style={{ padding: '16px', background: '#f8fafc', border: '1px dashed #cbd5e1', borderRadius: '6px', textAlign: 'center', color: '#64748b', fontSize: '13px' }}>
                  🔒 Ninguna pregunta ha sido jugada todavía. Se revelarán aquí una vez seleccionadas y marcadas como no disponibles por el docente.
                </div>
              ) : (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(120px, 1fr))', gap: '10px' }}>
                  {usedPCards.map((c) => (
                    <div
                      key={c.code}
                      onClick={() => setSelectedCard(c)}
                      style={{
                        border: '2px solid var(--blue)',
                        background: '#eff6ff',
                        borderRadius: '6px',
                        padding: '12px 8px',
                        textAlign: 'center',
                        cursor: 'pointer',
                        transition: 'all 0.15s ease',
                        boxShadow: '0 2px 4px rgba(0,0,0,0.05)',
                      }}
                      title={`${c.code}: Ya jugada / Clic para ver`}
                    >
                      <div style={{ fontSize: '20px', fontWeight: 'bold', color: 'var(--blue)', fontFamily: 'monospace' }}>
                        {c.code}
                      </div>
                      <div style={{ marginTop: '6px' }}>
                        <span
                          className="badge"
                          style={{
                            fontSize: '11px',
                            padding: '2px 6px',
                            background: '#fee2e2',
                            color: '#991b1b',
                            fontWeight: 'bold',
                          }}
                        >
                          NO DISPONIBLE
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Sección Retos Económicos (E) */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                <strong style={{ color: 'var(--green)', fontSize: '15px' }}>
                  📗 Retos Económicos Jugados: {usedECards.length} visibles ({countEAvailable} en el mazo)
                </strong>
              </div>

              {usedECards.length === 0 ? (
                <div style={{ padding: '16px', background: '#f8fafc', border: '1px dashed #cbd5e1', borderRadius: '6px', textAlign: 'center', color: '#64748b', fontSize: '13px' }}>
                  🔒 Ningún reto ha sido jugado todavía. Se revelarán aquí una vez seleccionados y marcados como no disponibles por el docente.
                </div>
              ) : (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(120px, 1fr))', gap: '10px' }}>
                  {usedECards.map((c) => (
                    <div
                      key={c.code}
                      onClick={() => setSelectedCard(c)}
                      style={{
                        border: '2px solid var(--green)',
                        background: '#f0fdf4',
                        borderRadius: '6px',
                        padding: '12px 8px',
                        textAlign: 'center',
                        cursor: 'pointer',
                        transition: 'all 0.15s ease',
                        boxShadow: '0 2px 4px rgba(0,0,0,0.05)',
                      }}
                      title={`${c.code}: Ya jugada / Clic para ver`}
                    >
                      <div style={{ fontSize: '20px', fontWeight: 'bold', color: 'var(--green)', fontFamily: 'monospace' }}>
                        {c.code}
                      </div>
                      <div style={{ marginTop: '6px' }}>
                        <span
                          className="badge"
                          style={{
                            fontSize: '11px',
                            padding: '2px 6px',
                            background: '#fee2e2',
                            color: '#991b1b',
                            fontWeight: 'bold',
                          }}
                        >
                          NO DISPONIBLE
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        );
      })()}

      {/* Historial Propio de Movimientos */}
      <div className="workspace">
        <h3 style={{ fontFamily: 'Georgia, serif', fontSize: '20px', marginBottom: '14px' }}>
          Últimos Movimientos de {status?.team_name}
        </h3>
        <div style={{ overflowX: 'auto' }}>
          <table className="table-audacity" style={{ fontSize: '14px' }}>
            <thead>
              <tr>
                <th>Hora</th>
                <th>Tipo</th>
                <th>Motivo</th>
                <th style={{ textAlign: 'right' }}>Monto</th>
              </tr>
            </thead>
            <tbody>
              {status?.history && status.history.length > 0 ? (
                status.history.map((h) => (
                  <tr key={h.id}>
                    <td>{h.timestamp}</td>
                    <td>
                      <span
                        className="badge"
                        style={{
                          backgroundColor: h.direction === 'credito' ? '#def7ec' : '#fde8e8',
                          color: h.direction === 'credito' ? '#03543f' : '#9b1c1c',
                        }}
                      >
                        {h.direction.toUpperCase()}
                      </span>
                    </td>
                    <td>{h.reason}</td>
                    <td style={{ textAlign: 'right', fontWeight: 'bold' }}>
                      {h.direction === 'credito' ? '+' : '-'} {h.amount_tdl} TDL
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={4} style={{ textAlign: 'center', color: '#556b62', padding: '20px' }}>
                    Aún no tenés movimientos registrados en esta partida.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal de Transferencia / Pago */}
      {showTransferModal && (
        <div className="modal-backdrop">
          <div className="modal-card" style={{ maxWidth: '480px' }}>
            <h3 style={{ font: '700 24px Georgia, serif', marginBottom: '14px' }}>Transferir desde Disponible</h3>
            <form onSubmit={handleTransferSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div>
                <label style={{ fontWeight: 'bold', fontSize: '13px', display: 'block', marginBottom: '4px' }}>
                  Destinatario:
                </label>
                <select
                  value={destAccountId}
                  onChange={(e) => setDestAccountId(Number(e.target.value))}
                  required
                  style={{ width: '100%', padding: '8px', border: '2px solid var(--ink)', background: '#fffdf5' }}
                >
                  <option value="">Seleccionar equipo o Banco...</option>
                  {status?.available_opponents.map((opp) => (
                    <option key={opp.id} value={opp.id}>
                      {opp.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label style={{ fontWeight: 'bold', fontSize: '13px', display: 'block', marginBottom: '4px' }}>
                  Monto a Transferir (TDL):
                </label>
                <input
                  type="number"
                  min={0.01}
                  step={0.01}
                  max={(status?.balance_available || 0) / 100}
                  value={transferAmountTDL}
                  onChange={(e) => setTransferAmountTDL(Number(e.target.value))}
                  required
                  style={{ width: '100%', padding: '8px', border: '2px solid var(--ink)' }}
                />
                <small style={{ color: '#556b62' }}>
                  Disponible actual: {((status?.balance_available || 0) / 100).toFixed(2)} TDL
                </small>
              </div>

              <div>
                <label style={{ fontWeight: 'bold', fontSize: '13px', display: 'block', marginBottom: '4px' }}>
                  Motivo:
                </label>
                <input
                  type="text"
                  value={transferReason}
                  onChange={(e) => setTransferReason(e.target.value)}
                  placeholder="Ej. Pago por servicio, préstamo acordado..."
                  required
                  style={{ width: '100%', padding: '8px', border: '2px solid var(--ink)' }}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '8px' }}>
                <button type="button" onClick={() => setShowTransferModal(false)} className="btn">
                  Cancelar
                </button>
                <button type="submit" disabled={transferring} className="btn btn-primary">
                  {transferring ? 'Transfiriendo...' : 'Confirmar Transferencia'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal de Tarjeta Abierta */}
      {selectedCard && (
        <div className="modal-backdrop">
          <div className="modal-card" style={{ maxWidth: '840px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
              <span className="badge" style={{ backgroundColor: selectedCard.deck_type === 'P' ? 'var(--blue)' : 'var(--green)', color: '#fff' }}>
                {selectedCard.code} · {selectedCard.deck_type === 'P' ? 'PREGUNTA' : 'RETO ECONÓMICO'}
              </span>
              <button onClick={() => setSelectedCard(null)} className="btn">
                Volver
              </button>
            </div>

            {selectedCard.deck_type === 'P' ? (
              <div style={{ padding: '20px', textAlign: 'center', background: '#f8fafc', borderRadius: '8px', border: '1px solid #cbd5e1' }}>
                <div style={{ fontSize: '48px', marginBottom: '8px' }}>📘</div>
                <h3 style={{ font: '700 24px Georgia, serif', marginBottom: '8px', color: 'var(--blue)' }}>
                  {selectedCard.title || `Tarjeta ${selectedCard.code}`}
                </h3>
                <div style={{ marginBottom: '16px' }}>
                  <span
                    className="badge"
                    style={{
                      fontSize: '13px',
                      padding: '4px 10px',
                      background: '#fee2e2',
                      color: '#991b1b',
                      fontWeight: 'bold',
                    }}
                  >
                    ESTADO: NO DISPONIBLE (JUGADA)
                  </span>
                </div>
                <p style={{ fontSize: '16px', color: '#1e293b', maxWidth: '560px', margin: '0 auto 16px auto', lineHeight: 1.6, fontWeight: 500 }}>
                  {selectedCard.text}
                </p>
                {selectedCard.image_path && (
                  <div style={{ maxWidth: '300px', margin: '0 auto 16px auto' }}>
                    <img
                      src={selectedCard.image_path}
                      alt={selectedCard.title}
                      style={{ width: '100%', border: '2px solid var(--ink)', borderRadius: '4px' }}
                    />
                  </div>
                )}
                <button onClick={() => setSelectedCard(null)} className="btn btn-primary">
                  Cerrar
                </button>
              </div>
            ) : (
              <div style={{ display: 'grid', gridTemplateColumns: 'minmax(200px, 320px) 1fr', gap: '20px', alignItems: 'center' }}>
                <div>
                  <img
                    src={selectedCard.image_path}
                    alt={selectedCard.title}
                    style={{ width: '100%', border: '2px solid var(--ink)', borderRadius: '4px' }}
                  />
                </div>
                <div>
                  <h3 style={{ font: '700 26px Georgia, serif', marginBottom: '10px' }}>{selectedCard.title}</h3>
                  <p style={{ fontSize: '18px', lineHeight: 1.6, marginBottom: '20px' }}>{selectedCard.text}</p>
                  <div style={{ borderTop: '1px solid #c0d0c4', paddingTop: '14px', fontSize: '13px', color: '#556b62' }}>
                    Estado: <span className="badge" style={{ background: '#fee2e2', color: '#991b1b', fontWeight: 'bold' }}>NO DISPONIBLE (JUGADA)</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
