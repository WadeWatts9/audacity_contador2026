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
  const [activePercentage, setActivePercentage] = useState<number | null>(null);
  const [customPercentage, setCustomPercentage] = useState<string>('');

  // Card filter & modals
  const [cardFilter, setCardFilter] = useState<'todas' | 'disponible' | 'no_disponible'>('todas');
  const [blockedCardNotice, setBlockedCardNotice] = useState<Card | null>(null);
  const [selectedCard, setSelectedCard] = useState<Card | null>(null);

  const availableBalanceTDL = (status?.balance_available || 0) / 100;

  const handleOpenTransferModal = () => {
    const initialAmount = availableBalanceTDL >= 50 ? 50 : availableBalanceTDL > 0 ? availableBalanceTDL : 0;
    setTransferAmountTDL(initialAmount);
    if (availableBalanceTDL > 0 && initialAmount > 0) {
      const pct = (initialAmount / availableBalanceTDL) * 100;
      setActivePercentage(pct <= 100 ? Number(pct.toFixed(1)) : null);
      setCustomPercentage(pct <= 100 ? pct.toFixed(1) : '');
    } else {
      setActivePercentage(null);
      setCustomPercentage('');
    }
    setShowTransferModal(true);
  };

  const handleSelectPercentage = (pct: number) => {
    setActivePercentage(pct);
    setCustomPercentage(String(pct));
    if (availableBalanceTDL <= 0) {
      setTransferAmountTDL(0);
      return;
    }
    const calculated = Math.floor(availableBalanceTDL * (pct / 100) * 100) / 100;
    setTransferAmountTDL(calculated);
  };

  const handleCustomPercentageChange = (val: string) => {
    setCustomPercentage(val);
    const num = parseFloat(val);
    if (!isNaN(num) && num >= 0 && num <= 100) {
      setActivePercentage(num);
      const calculated = Math.floor(availableBalanceTDL * (num / 100) * 100) / 100;
      setTransferAmountTDL(calculated);
    } else {
      setActivePercentage(null);
    }
  };

  const handleAmountChange = (val: number) => {
    setTransferAmountTDL(val);
    if (availableBalanceTDL > 0 && val >= 0) {
      const calculatedPct = (val / availableBalanceTDL) * 100;
      if (calculatedPct <= 100) {
        setActivePercentage(Number(calculatedPct.toFixed(1)));
        setCustomPercentage(calculatedPct.toFixed(1));
      } else {
        setActivePercentage(null);
        setCustomPercentage('');
      }
    } else {
      setActivePercentage(null);
      setCustomPercentage('');
    }
  };

  const handleCardClick = (card: Card) => {
    if (card.status !== 'resuelta_usada') {
      setBlockedCardNotice(card);
    } else {
      setSelectedCard(card);
    }
  };

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
            onClick={handleOpenTransferModal}
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

      {/* Tarjetas del Banco Central (Preguntas y Retos) */}
      <div className="workspace">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px', flexWrap: 'wrap', gap: '10px' }}>
          <div>
            <h3 style={{ fontFamily: 'Georgia, serif', fontSize: '20px', margin: 0 }}>
              Tarjetas del Banco Central (Preguntas y Retos)
            </h3>
            <small style={{ color: '#556b62', fontSize: '13px' }}>
              ℹ️ Haz clic en cualquier tarjeta para ver su estado o consultar la consigna si ya fue jugada.
            </small>
          </div>

          {/* Filtros de tarjetas: Todas / Disponibles / No Disponibles */}
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            <button
              onClick={() => setCardFilter('todas')}
              className={`btn ${cardFilter === 'todas' ? 'btn-primary' : ''}`}
              style={{ fontSize: '13px', padding: '5px 12px' }}
            >
              Todas (30)
            </button>
            <button
              onClick={() => setCardFilter('disponible')}
              className={`btn ${cardFilter === 'disponible' ? 'btn-primary' : ''}`}
              style={{ fontSize: '13px', padding: '5px 12px' }}
            >
              Disponibles ({countPAvailable + countEAvailable})
            </button>
            <button
              onClick={() => setCardFilter('no_disponible')}
              className={`btn ${cardFilter === 'no_disponible' ? 'btn-primary' : ''}`}
              style={{ fontSize: '13px', padding: '5px 12px' }}
            >
              No Disponibles ({30 - (countPAvailable + countEAvailable)})
            </button>
          </div>
        </div>

        {/* Banners P y E en dos colores (azul y verde) */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '14px', marginBottom: '20px' }}>
          <div className="deck-banner question" style={{ cursor: 'default' }}>
            <div>
              <strong>Preguntas (P)</strong>
              <small>Conceptos de economía</small>
            </div>
            <b>{countPAvailable} / 15 en mazo</b>
          </div>

          <div className="deck-banner economic" style={{ cursor: 'default' }}>
            <div>
              <strong>Retos Económicos (E)</strong>
              <small>Saldos, decisiones y compromisos</small>
            </div>
            <b>{countEAvailable} / 15 en mazo</b>
          </div>
        </div>

        {/* Cuadrícula de Tarjetas Pequeñas en dos colores */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(130px, 1fr))', gap: '10px' }}>
          {pDeck
            .concat(eDeck)
            .filter((c) => {
              if (cardFilter === 'disponible') return c.status !== 'resuelta_usada';
              if (cardFilter === 'no_disponible') return c.status === 'resuelta_usada';
              return true;
            })
            .map((c) => {
              const isUsed = c.status === 'resuelta_usada';
              const isEconomic = c.deck_type === 'E';
              return (
                <div
                  key={c.code}
                  onClick={() => handleCardClick(c)}
                  className={`card-item ${isEconomic ? 'economic' : ''} ${isUsed ? 'used' : ''}`}
                  style={{
                    cursor: 'pointer',
                    position: 'relative',
                  }}
                  title={
                    isUsed
                      ? `${c.code}: No disponible (Ya jugada). Clic para abrir vista previa`
                      : `${c.code}: Disponible en mazo. Clic para ver información`
                  }
                >
                  <div
                    className="stripe"
                    style={{
                      backgroundColor: isEconomic ? 'var(--green)' : 'var(--blue)',
                      opacity: isUsed ? 0.75 : 1,
                    }}
                  ></div>
                  <strong>{c.code}</strong>
                  <small>{isUsed ? c.title : (isEconomic ? 'Reto Económico' : 'Pregunta')}</small>
                  <span
                    style={{
                      fontSize: '10px',
                      marginTop: '4px',
                      fontWeight: 'bold',
                      padding: '2px 4px',
                      borderRadius: '3px',
                      background: isUsed ? '#fee2e2' : '#dcfce7',
                      color: isUsed ? '#991b1b' : '#166534',
                    }}
                  >
                    {isUsed ? 'NO DISPONIBLE' : 'DISPONIBLE'}
                  </span>
                </div>
              );
            })}
        </div>
      </div>

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

      {/* Modal de Transferencia / Pago con Montos Específicos y Porcentajes */}
      {showTransferModal && (
        <div className="modal-backdrop">
          <div className="modal-card" style={{ maxWidth: '520px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
              <h3 style={{ font: '700 24px Georgia, serif', margin: 0 }}>Transferir / Pagar</h3>
              <button
                type="button"
                onClick={() => setShowTransferModal(false)}
                className="btn"
                style={{ padding: '4px 10px' }}
              >
                ✕
              </button>
            </div>

            {/* Saldo disponible de referencia */}
            <div
              style={{
                background: '#fffdf5',
                border: '1.5px solid var(--ink)',
                borderRadius: '6px',
                padding: '12px 16px',
                marginBottom: '16px',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}
            >
              <div>
                <small style={{ color: '#556b62', textTransform: 'uppercase', fontWeight: 'bold', fontSize: '11px' }}>
                  Saldo Disponible para Operaciones
                </small>
                <div style={{ font: '700 22px Georgia, serif', color: 'var(--green)' }}>
                  TDL {availableBalanceTDL.toLocaleString('es-UY', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <span className="badge" style={{ background: '#def7ec', color: '#03543f', fontWeight: 'bold' }}>
                  Cuenta Operativa
                </span>
              </div>
            </div>

            <form onSubmit={handleTransferSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              {/* Destinatario */}
              <div>
                <label style={{ fontWeight: 'bold', fontSize: '13px', display: 'block', marginBottom: '4px' }}>
                  Destinatario del Pago o Transferencia:
                </label>
                <select
                  value={destAccountId}
                  onChange={(e) => setDestAccountId(Number(e.target.value))}
                  required
                  style={{ width: '100%', padding: '10px', border: '2px solid var(--ink)', background: '#fffdf5', fontSize: '14px' }}
                >
                  <option value="">Seleccionar equipo o Banco Central...</option>
                  {status?.available_opponents.map((opp) => (
                    <option key={opp.id} value={opp.id}>
                      {opp.name}
                    </option>
                  ))}
                </select>
              </div>

              {/* Selector de Monto / Porcentaje */}
              <div style={{ background: '#f8fafc', border: '1px solid #cbd5e1', borderRadius: '6px', padding: '14px' }}>
                <label style={{ fontWeight: 'bold', fontSize: '13px', display: 'block', marginBottom: '8px' }}>
                  Monto a Transferir (Específico o Porcentaje de Saldo):
                </label>

                {/* Botones de Porcentaje Rápido */}
                <div style={{ marginBottom: '10px' }}>
                  <div style={{ fontSize: '12px', color: '#475569', marginBottom: '6px', fontWeight: 600 }}>
                    Calcular por % de tu saldo disponible:
                  </div>
                  <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                    {[10, 20, 25, 50, 75, 100].map((pct) => (
                      <button
                        key={pct}
                        type="button"
                        onClick={() => handleSelectPercentage(pct)}
                        disabled={availableBalanceTDL <= 0}
                        className="btn"
                        style={{
                          padding: '4px 10px',
                          fontSize: '12px',
                          background: activePercentage === pct ? 'var(--blue)' : '#ffffff',
                          color: activePercentage === pct ? '#ffffff' : 'var(--ink)',
                          border: '1.5px solid var(--ink)',
                          fontWeight: 'bold',
                          transition: 'all 0.15s ease',
                        }}
                      >
                        {pct === 100 ? '100% (Todo)' : `${pct}%`}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Inputs de Monto TDL y Porcentaje Manual */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', alignItems: 'flex-start' }}>
                  <div>
                    <label style={{ fontSize: '12px', color: '#334155', display: 'block', marginBottom: '3px', fontWeight: 600 }}>
                      Monto Específico (TDL):
                    </label>
                    <input
                      type="number"
                      min={0.01}
                      step={0.01}
                      max={availableBalanceTDL}
                      value={transferAmountTDL || ''}
                      onChange={(e) => handleAmountChange(parseFloat(e.target.value) || 0)}
                      required
                      placeholder="0.00"
                      style={{
                        width: '100%',
                        padding: '8px 10px',
                        fontSize: '15px',
                        fontWeight: 'bold',
                        border: '2px solid var(--ink)',
                        boxSizing: 'border-box',
                      }}
                    />
                  </div>

                  <div>
                    <label style={{ fontSize: '12px', color: '#334155', display: 'block', marginBottom: '3px', fontWeight: 600 }}>
                      O Porcentaje Manual (%):
                    </label>
                    <div style={{ display: 'flex', alignItems: 'center' }}>
                      <input
                        type="number"
                        min={0.1}
                        max={100}
                        step={0.1}
                        value={customPercentage}
                        onChange={(e) => handleCustomPercentageChange(e.target.value)}
                        placeholder="Ej. 15"
                        disabled={availableBalanceTDL <= 0}
                        style={{
                          width: '100%',
                          padding: '8px 10px',
                          fontSize: '15px',
                          fontWeight: 'bold',
                          border: '2px solid var(--ink)',
                          boxSizing: 'border-box',
                        }}
                      />
                      <span style={{ marginLeft: '6px', fontWeight: 'bold', fontSize: '15px', color: '#475569' }}>%</span>
                    </div>
                  </div>
                </div>

                {/* Desglose dinámico */}
                <div
                  style={{
                    marginTop: '10px',
                    padding: '8px 10px',
                    background: '#ffffff',
                    borderRadius: '4px',
                    border: '1px dashed #cbd5e1',
                    fontSize: '12px',
                    color: '#334155',
                  }}
                >
                  <div>
                    • <strong>Monto a enviar:</strong> {transferAmountTDL.toFixed(2)} TDL{' '}
                    {availableBalanceTDL > 0 && (
                      <span style={{ color: 'var(--blue)', fontWeight: 600 }}>
                        ({((transferAmountTDL / availableBalanceTDL) * 100).toFixed(1)}% del disponible)
                      </span>
                    )}
                  </div>
                  <div>
                    • <strong>Saldo disponible restante estimado:</strong>{' '}
                    <span style={{ color: availableBalanceTDL - transferAmountTDL < 0 ? 'var(--red)' : '#166534', fontWeight: 'bold' }}>
                      {Math.max(0, availableBalanceTDL - transferAmountTDL).toFixed(2)} TDL
                    </span>
                  </div>
                </div>
              </div>

              {/* Motivo */}
              <div>
                <label style={{ fontWeight: 'bold', fontSize: '13px', display: 'block', marginBottom: '4px' }}>
                  Motivo / Concepto:
                </label>
                <input
                  type="text"
                  value={transferReason}
                  onChange={(e) => setTransferReason(e.target.value)}
                  placeholder="Ej. Pago de arancel bancario, compra de propiedad, etc."
                  required
                  style={{ width: '100%', padding: '8px 10px', border: '2px solid var(--ink)', fontSize: '14px', boxSizing: 'border-box' }}
                />
              </div>

              {/* Botones de acción */}
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '6px' }}>
                <button type="button" onClick={() => setShowTransferModal(false)} className="btn">
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={transferring || transferAmountTDL <= 0 || transferAmountTDL > availableBalanceTDL}
                  className="btn btn-primary"
                >
                  {transferring ? 'Procesando...' : 'Confirmar Transferencia'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal Informativo: Tarjeta Disponible en el Mazo (No Visible para Equipos) */}
      {blockedCardNotice && (
        <div className="modal-backdrop">
          <div className="modal-card" style={{ maxWidth: '500px', textAlign: 'center' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
              <span
                className="badge"
                style={{
                  backgroundColor: blockedCardNotice.deck_type === 'P' ? 'var(--blue)' : 'var(--green)',
                  color: '#fff',
                  fontSize: '13px',
                  padding: '4px 10px',
                }}
              >
                {blockedCardNotice.code} · {blockedCardNotice.deck_type === 'P' ? 'PREGUNTA (P)' : 'RETO ECONÓMICO (E)'}
              </span>
              <span
                className="badge"
                style={{
                  background: '#dcfce7',
                  color: '#166534',
                  fontWeight: 'bold',
                  fontSize: '12px',
                }}
              >
                DISPONIBLE EN EL MAZO
              </span>
            </div>

            <div style={{ fontSize: '50px', marginBottom: '10px' }}>🔒</div>

            <h3 style={{ font: '700 22px Georgia, serif', marginBottom: '10px', color: 'var(--ink)' }}>
              Contenido No Disponible para Equipos
            </h3>

            <div
              style={{
                background: '#fffdf5',
                border: '1.5px dashed #c0d0c4',
                borderRadius: '8px',
                padding: '16px',
                marginBottom: '18px',
                textAlign: 'left',
                fontSize: '14px',
                lineHeight: '1.6',
                color: '#2b453e',
              }}
            >
              <p style={{ margin: '0 0 10px 0' }}>
                La tarjeta <strong>{blockedCardNotice.code}</strong> se encuentra actualmente <strong>disponible en el mazo del Banco Central</strong>.
              </p>
              <p style={{ margin: 0 }}>
                ⚠️ <strong>Regla del juego:</strong> Por normas de transparencia y equidad, los equipos no pueden ver el contenido de las preguntas ni de los retos mientras permanezcan disponibles.
                <br /><br />
                👉 Podrás ver la consigna completa de esta tarjeta una vez que el docente administrador la seleccione y la marque como <strong>NO DISPONIBLE</strong> (jugada).
              </p>
            </div>

            <button
              onClick={() => setBlockedCardNotice(null)}
              className="btn btn-primary"
              style={{ width: '100%', padding: '10px', fontSize: '15px' }}
            >
              Entendido
            </button>
          </div>
        </div>
      )}

      {/* Modal de Vista Previa de Tarjeta Jugada / No Disponible */}
      {selectedCard && (
        <div className="modal-backdrop">
          <div className="modal-card" style={{ maxWidth: '820px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span
                  className="badge"
                  style={{
                    backgroundColor: selectedCard.deck_type === 'P' ? 'var(--blue)' : 'var(--green)',
                    color: '#fff',
                    fontSize: '14px',
                    padding: '4px 10px',
                  }}
                >
                  {selectedCard.code} · {selectedCard.deck_type === 'P' ? 'PREGUNTA (P)' : 'RETO ECONÓMICO (E)'}
                </span>
                <span
                  className="badge"
                  style={{
                    background: '#fee2e2',
                    color: '#991b1b',
                    fontWeight: 'bold',
                    fontSize: '12px',
                  }}
                >
                  NO DISPONIBLE (JUGADA)
                </span>
              </div>
              <button onClick={() => setSelectedCard(null)} className="btn" style={{ padding: '4px 10px' }}>
                ✕
              </button>
            </div>

            {selectedCard.deck_type === 'P' ? (
              <div style={{ padding: '24px', textAlign: 'center', background: '#f8fafc', borderRadius: '8px', border: '1px solid #cbd5e1' }}>
                <div style={{ fontSize: '48px', marginBottom: '8px' }}>📘</div>
                <h3 style={{ font: '700 24px Georgia, serif', marginBottom: '8px', color: 'var(--blue)' }}>
                  {selectedCard.title || `Tarjeta ${selectedCard.code}`}
                </h3>
                <p style={{ fontSize: '17px', color: '#1e293b', maxWidth: '620px', margin: '0 auto 16px auto', lineHeight: 1.6, fontWeight: 500 }}>
                  {selectedCard.text}
                </p>
                {selectedCard.image_path && (
                  <div style={{ maxWidth: '320px', margin: '0 auto 16px auto' }}>
                    <img
                      src={selectedCard.image_path}
                      alt={selectedCard.title}
                      style={{ width: '100%', border: '2px solid var(--ink)', borderRadius: '4px' }}
                    />
                  </div>
                )}
                <div style={{ borderTop: '1px solid #e2e8f0', paddingTop: '14px', marginTop: '14px' }}>
                  <button onClick={() => setSelectedCard(null)} className="btn btn-primary" style={{ padding: '8px 24px' }}>
                    Cerrar Vista Previa
                  </button>
                </div>
              </div>
            ) : (
              <div>
                <div style={{ display: 'grid', gridTemplateColumns: selectedCard.image_path ? 'minmax(200px, 320px) 1fr' : '1fr', gap: '20px', alignItems: 'center' }}>
                  {selectedCard.image_path && (
                    <div>
                      <img
                        src={selectedCard.image_path}
                        alt={selectedCard.title}
                        style={{ width: '100%', border: '2px solid var(--ink)', borderRadius: '4px' }}
                      />
                    </div>
                  )}
                  <div>
                    <h3 style={{ font: '700 26px Georgia, serif', marginBottom: '12px', color: 'var(--green)' }}>
                      {selectedCard.title}
                    </h3>
                    <p style={{ fontSize: '17px', lineHeight: 1.6, marginBottom: '20px', color: '#1e293b' }}>
                      {selectedCard.text}
                    </p>
                    <div style={{ borderTop: '1px solid #c0d0c4', paddingTop: '14px', fontSize: '13px', color: '#556b62' }}>
                      ℹ️ Esta tarjeta de Reto Económico ya fue ejecutada o marcada como no disponible por el docente.
                    </div>
                  </div>
                </div>
                <div style={{ borderTop: '1px solid #e2e8f0', paddingTop: '14px', marginTop: '16px', textAlign: 'right' }}>
                  <button onClick={() => setSelectedCard(null)} className="btn btn-primary" style={{ padding: '8px 24px' }}>
                    Cerrar Vista Previa
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
