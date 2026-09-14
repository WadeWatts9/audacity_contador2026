import React, { useState, useEffect } from 'react';
import { useGame } from '../../context/GameContext';
import { useAuth } from '../../context/AuthContext';
import { api, getAuthToken } from '../../api/client';
import { BoardSquare, Card, TeamCredentials } from '../../types';
import {
  Play, DollarSign, RotateCcw, AlertTriangle, Download, PlusCircle,
  Eye, CheckCircle2, XCircle, ArrowRightLeft, ShieldCheck, Dices, Layers,
  Flag, FileText
} from 'lucide-react';

export const TeacherDashboard: React.FC = () => {
  const { gameCode, setGameCode, summary, feed, pDeck, eDeck, countPAvailable, countEAvailable, refreshGame } = useGame();
  const { user } = useAuth();

  // Estados para creación de partida
  const [showCreateModal, setShowCreateModal] = useState(!gameCode);
  const [newGameName, setNewGameName] = useState('Partida Audacity 2026');
  const [newGameProfile, setNewGameProfile] = useState<'genially' | 'prezi'>('genially');
  const [initialTeamTDL, setInitialTeamTDL] = useState(10000);
  const [initialBankTDL, setInitialBankTDL] = useState(100000);
  const [createdCredentials, setCreatedCredentials] = useState<TeamCredentials[] | null>(null);

  // Estados para turnos y casillas
  const [squares, setSquares] = useState<BoardSquare[]>([]);
  const [selectedSquareId, setSelectedSquareId] = useState<number>(1);
  const [diceRoll, setDiceRoll] = useState<number>(3);
  const [advancingTurn, setAdvancingTurn] = useState(false);

  // Estados para cartas
  const [adminPDeck, setAdminPDeck] = useState<Card[]>([]);
  const [showAdminPModal, setShowAdminPModal] = useState(false);
  const [activeCard, setActiveCard] = useState<Card | null>(null);
  const [activeCardInstanceId, setActiveCardInstanceId] = useState<number | null>(null);
  const [selectedPVariant, setSelectedPVariant] = useState<string>('var_100_60');
  const [targetTeamId, setTargetTeamId] = useState<number | ''>('');
  const [eDiceRolls, setEDiceRolls] = useState<number[]>([4, 4, 4]);
  const [acceptInsurance, setAcceptInsurance] = useState<boolean>(true);
  const [inspectingUsedCard, setInspectingUsedCard] = useState<Card | null>(null);
  const [cardFilter, setCardFilter] = useState<'all' | 'disponible' | 'no_disponible'>('all');


  // Estados para efectos configurables de Preguntas P
  const [pEffectMode, setPEffectMode] = useState<'percentage' | 'fixed' | 'otros'>('percentage');
  const [pCustomGainPct, setPCustomGainPct] = useState<number>(100);
  const [pCustomLossPct, setPCustomLossPct] = useState<number>(60);
  const [pFixedGainTDL, setPFixedGainTDL] = useState<number>(3000);
  const [pFixedLossTDL, setPFixedLossTDL] = useState<number>(1500);
  const [pOtherDescription, setPOtherDescription] = useState<string>('');

  // Estados para Fin de Partida y PDF
  const [showEndGameModal, setShowEndGameModal] = useState<boolean>(false);
  const [endingGame, setEndingGame] = useState<boolean>(false);
  const [downloadingPdf, setDownloadingPdf] = useState<boolean>(false);

  // Estados para Limpiar Base de Datos
  const [showCleanDbModal, setShowCleanDbModal] = useState<boolean>(false);
  const [cleaningDb, setCleaningDb] = useState<boolean>(false);

  // Estados para operaciones bancarias
  const [showBankModal, setShowBankModal] = useState(false);
  const [bankOpType, setBankOpType] = useState<'pay' | 'collect' | 'transfer' | 'adjust' | 'zero'>('pay');
  const [selectedTeamId, setSelectedTeamId] = useState<number | ''>('');
  const [destTeamId, setDestTeamId] = useState<number | ''>('');
  const [opAmountTDL, setOpAmountTDL] = useState<number>(100);
  const [opReason, setOpReason] = useState<string>('');
  const [targetAdjustTDL, setTargetAdjustTDL] = useState<number>(0);
  const [resolveContracts, setResolveContracts] = useState<boolean>(false);

  useEffect(() => {
    api.getBoardSquares().then(setSquares).catch(console.error);
  }, []);

  const handleCreateGame = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await api.createGame({
        name: newGameName,
        profile: newGameProfile,
        initial_team_balance: initialTeamTDL * 100,
        initial_bank_balance: initialBankTDL * 100,
      });
      setGameCode(res.code);
      if (res.credentials_sheet) {
        setCreatedCredentials(res.credentials_sheet);
      }
      setShowCreateModal(false);
      refreshGame();
    } catch (err: any) {
      alert('Error creando partida: ' + err.message);
    }
  };

  const handleAdvanceTurn = async () => {
    if (!gameCode) return;
    setAdvancingTurn(true);
    try {
      await api.advanceTurn(gameCode, {
        dice_roll: diceRoll,
        square_id: selectedSquareId,
      });
      refreshGame();
    } catch (err: any) {
      alert('Error al avanzar turno: ' + err.message);
    } finally {
      setAdvancingTurn(false);
    }
  };

  const handleDrawCard = async (type: 'P' | 'E', specificCode?: string) => {
    if (!gameCode) return;
    try {
      const drawn = await api.drawCard(gameCode, type, specificCode);
      setActiveCard(drawn);
      setActiveCardInstanceId(drawn.instance_id);
      refreshGame();
    } catch (err: any) {
      alert('Error al extraer tarjeta: ' + err.message);
    }
  };

  const handleCardItemClick = (c: Card) => {
    if (c.status === 'resuelta_usada') {
      setInspectingUsedCard(c);
    } else {
      handleDrawCard(c.deck_type, c.code);
    }
  };

  const handleMarkActiveUnavailable = async () => {
    if (!gameCode || !activeCard) return;
    try {
      await api.setCardStatus(gameCode, activeCard.code, 'resuelta_usada');
      alert(`Tarjeta ${activeCard.code} marcada como NO DISPONIBLE.`);
      setActiveCard(null);
      setActiveCardInstanceId(null);
      refreshGame();
    } catch (err: any) {
      alert('Error al marcar tarjeta: ' + err.message);
    }
  };

  const handleReactivateCard = async (cardCode: string) => {
    if (!gameCode) return;
    try {
      await api.setCardStatus(gameCode, cardCode, 'disponible');
      alert(`Tarjeta ${cardCode} reactivada como DISPONIBLE en el mazo.`);
      setInspectingUsedCard(null);
      refreshGame();
    } catch (err: any) {
      alert('Error reactivando tarjeta: ' + err.message);
    }
  };


  const handleValidateP = async (isCorrect: boolean) => {
    if (!activeCardInstanceId) return;

    if (pEffectMode === 'otros' && !pOtherDescription.trim()) {
      alert('Por favor ingresá una descripción obligatoria para el efecto "Otros" antes de validar.');
      return;
    }

    try {
      const res = await api.validatePCard({
        instance_id: activeCardInstanceId,
        is_correct: isCorrect,
        variant_id: selectedPVariant,
        effect_type: pEffectMode,
        gain_pct: pEffectMode === 'percentage' && selectedPVariant === 'custom' ? pCustomGainPct : undefined,
        loss_pct: pEffectMode === 'percentage' && selectedPVariant === 'custom' ? pCustomLossPct : undefined,
        gain_amount_tdl: pEffectMode === 'fixed' ? pFixedGainTDL : undefined,
        loss_amount_tdl: pEffectMode === 'fixed' ? pFixedLossTDL : undefined,
        other_description: pEffectMode === 'otros' ? pOtherDescription.trim() : undefined,
      });
      alert(res.message);
      if (res.enables_e_card) {
        // Casilla 2 encadenada a Reto Económico en el mismo turno
        await handleDrawCard('E');
      } else {
        setActiveCard(null);
        setActiveCardInstanceId(null);
        setPOtherDescription('');
      }
      refreshGame();
    } catch (err: any) {
      alert('Error al validar pregunta: ' + err.message);
    }
  };

  const handleEndGame = async () => {
    if (!gameCode) return;
    setEndingGame(true);
    try {
      const res = await api.endGame(gameCode);
      alert(res.message);
      setShowEndGameModal(false);
      refreshGame();
    } catch (err: any) {
      alert('Error al finalizar partida: ' + err.message);
    } finally {
      setEndingGame(false);
    }
  };

  const handleDownloadPdf = async () => {
    if (!gameCode) return;
    setDownloadingPdf(true);
    try {
      const token = getAuthToken();
      const res = await fetch(`/api/games/${gameCode}/export-pdf`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!res.ok) throw new Error('Error al generar el PDF de auditoría.');
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `audacity_auditoria_${gameCode}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      alert(err.message || 'Error descargando PDF');
    } finally {
      setDownloadingPdf(false);
    }
  };

  const handleExecuteE = async () => {
    if (!activeCardInstanceId) return;
    try {
      const res = await api.executeECard({
        instance_id: activeCardInstanceId,
        target_account_id: targetTeamId ? Number(targetTeamId) : undefined,
        dice_rolls: eDiceRolls,
        accept_insurance: acceptInsurance,
      });
      alert('Reto ejecutado correctamente.');
      setActiveCard(null);
      setActiveCardInstanceId(null);
      refreshGame();
    } catch (err: any) {
      alert('Error al ejecutar reto: ' + err.message);
    }
  };

  const handleBankSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const amountCents = Math.round(opAmountTDL * 100);
      if (bankOpType === 'pay') {
        await api.payToTeam({ team_account_id: Number(selectedTeamId), amount_cents: amountCents, reason: opReason });
      } else if (bankOpType === 'collect') {
        await api.collectFromTeam({ team_account_id: Number(selectedTeamId), amount_cents: amountCents, reason: opReason });
      } else if (bankOpType === 'transfer') {
        await api.transfer({ source_account_id: Number(selectedTeamId), destination_account_id: Number(destTeamId), amount_cents: amountCents, reason: opReason });
      } else if (bankOpType === 'adjust') {
        await api.adjustBalance({ account_id: Number(selectedTeamId), target_available_cents: Math.round(targetAdjustTDL * 100), reason: opReason });
      } else if (bankOpType === 'zero') {
        await api.setZero({ account_id: Number(selectedTeamId), reason: opReason, resolve_contracts_explicitly: resolveContracts });
      }
      setShowBankModal(false);
      setOpReason('');
      refreshGame();
    } catch (err: any) {
      alert('Error en operación bancaria: ' + err.message);
    }
  };

  const handleUndo = async (entryId: number) => {
    if (!confirm('¿Seguro que deseás revertir esta transacción y su estado asociado?')) return;
    try {
      await api.undoTransaction({ entry_id: entryId });
      alert('Transacción revertida con éxito.');
      refreshGame();
    } catch (err: any) {
      alert('Error al deshacer: ' + err.message);
    }
  };

  const handleOpenAdminPDeck = async () => {
    if (!gameCode) return;
    try {
      const pCatalog = await api.getAdminPDeck(gameCode);
      setAdminPDeck(pCatalog);
      setShowAdminPModal(true);
    } catch (err: any) {
      alert('Error cargando respuestas docentes: ' + err.message);
    }
  };

  const handleResetDecks = async () => {
    if (!gameCode) return;
    if (!confirm('¿Reiniciar los dos mazos? Las tarjetas volverán a estar disponibles sin alterar contratos vigentes.')) return;
    try {
      await api.resetDecks(gameCode);
      refreshGame();
      alert('Mazos reiniciados.');
    } catch (err: any) {
      alert('Error reiniciando mazos: ' + err.message);
    }
  };

  const handleCleanDatabase = async () => {
    setCleaningDb(true);
    try {
      const res = await api.cleanDatabase();
      alert(res.message || 'Base de datos reiniciada con éxito.');
      setShowCleanDbModal(false);
      setGameCode('');
      setCreatedCredentials(null);
      refreshGame();
      setShowCreateModal(true);
    } catch (err: any) {
      alert('Error limpiando base de datos: ' + err.message);
    } finally {
      setCleaningDb(false);
    }
  };

  const activeSquare = squares.find((s) => s.id === selectedSquareId);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Top Banner: Banco y Turno Activo */}
      <div className="workspace" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <span style={{ fontSize: '13px', fontWeight: 'bold', color: '#405c50', textTransform: 'uppercase' }}>Fondos del Banco Central</span>
          <div style={{ font: '900 32px Georgia, serif', color: 'var(--red)' }}>
            TDL {((summary?.bank_balance || 0) / 100).toLocaleString('es-UY', { minimumFractionDigits: 2 })}
          </div>
        </div>

        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
          <button onClick={() => setShowCreateModal(true)} className="btn">
            <PlusCircle size={16} />
            <span>Nueva Partida</span>
          </button>
          <button onClick={() => { setBankOpType('pay'); setShowBankModal(true); }} className="btn btn-primary">
            <DollarSign size={16} />
            <span>Operar Banco</span>
          </button>
          <button onClick={handleOpenAdminPDeck} className="btn btn-blue" title="Ver respuestas protegidas">
            <Eye size={16} />
            <span>Claves Docente (P01-P15)</span>
          </button>
          <button onClick={handleDownloadPdf} disabled={downloadingPdf} className="btn" title="Descargar informe oficial en PDF">
            <FileText size={16} />
            <span>{downloadingPdf ? 'Generando...' : 'PDF Auditoría'}</span>
          </button>
          <a
            href="/guia_estudiante_audacity.pdf"
            target="_blank"
            rel="noopener noreferrer"
            className="btn"
            style={{ textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '6px' }}
            title="Ver y descargar la Guía de Uso del Estudiante en PDF"
          >
            <FileText size={16} />
            <span>Guía Alumnos (PDF)</span>
          </a>
          <button onClick={handleResetDecks} className="btn" title="Reiniciar disponibilidad de tarjetas">
            <RotateCcw size={16} />
            <span>Reiniciar Mazos</span>
          </button>
          {summary?.game.status !== 'finalizada' && (
            <button
              onClick={() => setShowEndGameModal(true)}
              className="btn btn-red"
              style={{ fontWeight: 'bold', background: '#dc2626', color: '#fff' }}
              title="Cerrar y fijar la partida actual"
            >
              <Flag size={16} />
              <span>FIN DE PARTIDA</span>
            </button>
          )}
          <button
            onClick={() => setShowCleanDbModal(true)}
            className="btn"
            style={{ fontWeight: 'bold', color: '#b91c1c', borderColor: '#fca5a5', background: '#fef2f2' }}
            title="Eliminar todas las partidas y reiniciar la base de datos a cero"
          >
            <AlertTriangle size={16} color="#b91c1c" />
            <span>Limpiar DB</span>
          </button>
        </div>
      </div>

      {/* Banner de Partida Finalizada */}
      {summary?.game.status === 'finalizada' && (
        <div
          style={{
            background: '#fef3c7',
            border: '2px solid #d97706',
            borderRadius: '6px',
            padding: '16px 20px',
            color: '#92400e',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: '12px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span style={{ fontSize: '28px' }}>🏁</span>
            <div>
              <strong style={{ fontSize: '18px', display: 'block' }}>PARTIDA FINALIZADA · TABLERO Y CUENTAS FIJADAS</strong>
              <span style={{ fontSize: '14px' }}>
                La partida está cerrada. No se permiten nuevas tiradas ni transferencias. El podio final ha quedado consolidado.
              </span>
            </div>
          </div>
          <button onClick={handleDownloadPdf} disabled={downloadingPdf} className="btn btn-primary" style={{ background: '#b45309', border: 'none' }}>
            <FileText size={16} />
            <span>{downloadingPdf ? 'Generando PDF...' : 'Descargar Informe de Auditoría PDF'}</span>
          </button>
        </div>
      )}

      {/* Control de Turno y Casilla */}
      <div className="workspace">
        <h3 style={{ fontFamily: 'Georgia, serif', fontSize: '20px', marginBottom: '14px', borderBottom: '2px solid var(--ink)', paddingBottom: '6px' }}>
          Control de Turno y Casilla
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '16px', alignItems: 'flex-end' }}>
          <div>
            <label style={{ fontWeight: 'bold', fontSize: '14px', display: 'block', marginBottom: '6px' }}>
              Equipo Activo en Turno:
            </label>
            <div style={{ padding: '10px 14px', background: '#e1f1fb', border: '2px solid var(--ink)', fontWeight: 'bold', fontSize: '17px' }}>
              {summary?.active_team_name || 'Sin equipo asignado'} (Ronda {summary?.game?.current_turn_number || 1})
            </div>
          </div>

          <div>
            <label style={{ fontWeight: 'bold', fontSize: '14px', display: 'block', marginBottom: '6px' }}>
              Casilla donde cayó la ficha:
            </label>
            <select
              value={selectedSquareId}
              onChange={(e) => setSelectedSquareId(Number(e.target.value))}
              style={{ width: '100%', padding: '10px', border: '2px solid var(--ink)', background: '#fffdf5', fontSize: '14px', fontWeight: 'bold' }}
            >
              {squares.map((sq) => (
                <option key={sq.id} value={sq.id}>
                  Casilla {sq.id}: {sq.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label style={{ fontWeight: 'bold', fontSize: '14px', display: 'block', marginBottom: '6px' }}>
              Dado Físico (1-6):
            </label>
            <div style={{ display: 'flex', gap: '8px' }}>
              <input
                type="number"
                min={1}
                max={6}
                value={diceRoll}
                onChange={(e) => setDiceRoll(Number(e.target.value))}
                style={{ width: '80px', padding: '10px', border: '2px solid var(--ink)', fontSize: '16px', textAlign: 'center', fontWeight: 'bold', background: '#fffdf5' }}
              />
              <button
                type="button"
                onClick={() => setDiceRoll(Math.floor(Math.random() * 6) + 1)}
                className="btn"
                title="Tirada digital aleatoria"
              >
                <Dices size={16} />
              </button>
            </div>
          </div>

          <div>
            <button
              onClick={handleAdvanceTurn}
              disabled={advancingTurn}
              className="btn btn-green"
              style={{ width: '100%', padding: '12px', justifyContent: 'center' }}
            >
              <Play size={18} />
              <span>{advancingTurn ? 'Avanzando...' : 'Avanzar Turno (Pasos 1 a 4)'}</span>
            </button>
          </div>
        </div>

        {activeSquare && (
          <div style={{ marginTop: '14px', background: '#fffdf5', border: '1px solid #c0d0c4', padding: '10px 14px', borderRadius: '4px', fontSize: '13px' }}>
            <strong>Efecto de Casilla {activeSquare.id}:</strong> {activeSquare.description}
          </div>
        )}
      </div>

      {/* Validación de Tarjeta Activa (si hay una abierta) */}
      {activeCard && (
        <div className="workspace" style={{ border: '3px solid var(--red)', background: '#fffdf5' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <span className="badge" style={{ backgroundColor: activeCard.deck_type === 'P' ? 'var(--blue)' : 'var(--green)', color: 'white' }}>
              TARJETA ACTIVA: {activeCard.code} ({activeCard.deck_type === 'P' ? 'Pregunta' : 'Reto Económico'})
            </span>
            <button onClick={() => { setActiveCard(null); setActiveCardInstanceId(null); }} className="btn" style={{ padding: '4px 8px' }}>
              Cerrar
            </button>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'minmax(240px, 320px) 1fr', gap: '20px', alignItems: 'center' }}>
            <div>
              <img src={activeCard.image_path} alt={activeCard.title} style={{ width: '100%', border: '2px solid var(--ink)', borderRadius: '4px' }} />
            </div>

            <div>
              <h4 style={{ font: '700 24px Georgia, serif', marginBottom: '10px' }}>{activeCard.title}</h4>
              <p style={{ fontSize: '17px', lineHeight: 1.5, marginBottom: '16px' }}>{activeCard.text}</p>

              {/* Si es Pregunta P */}
              {activeCard.deck_type === 'P' && (
                <div style={{ background: '#e1f1fb', border: '2px solid var(--blue)', padding: '14px', borderRadius: '4px', marginBottom: '16px' }}>
                  <div style={{ fontWeight: 'bold', color: 'var(--blue)', marginBottom: '4px' }}>
                    Clave de Respuesta Docente:
                  </div>
                  <div style={{ fontSize: '15px', fontWeight: 600 }}>{activeCard.teacher_answer || 'Consultá la clave docente.'}</div>
                  {activeCard.source && <div style={{ fontSize: '12px', color: '#405c50', marginTop: '4px' }}>Fuente: {activeCard.source}</div>}

                  <div style={{ marginTop: '14px', background: '#fff', padding: '12px', borderRadius: '4px', border: '1px solid #c0d0c4' }}>
                    <label style={{ display: 'block', fontSize: '13px', fontWeight: 'bold', marginBottom: '8px' }}>
                      Efecto al Acertar o Errar:
                    </label>

                    {/* Selector de tipo de efecto */}
                    <div style={{ display: 'flex', gap: '6px', marginBottom: '12px', flexWrap: 'wrap' }}>
                      <button
                        type="button"
                        onClick={() => setPEffectMode('percentage')}
                        className={`btn ${pEffectMode === 'percentage' ? 'btn-primary' : ''}`}
                        style={{ padding: '6px 10px', fontSize: '12px' }}
                      >
                        % Porcentajes
                      </button>
                      <button
                        type="button"
                        onClick={() => setPEffectMode('fixed')}
                        className={`btn ${pEffectMode === 'fixed' ? 'btn-primary' : ''}`}
                        style={{ padding: '6px 10px', fontSize: '12px' }}
                      >
                        💵 Montos Fijos (TDL)
                      </button>
                      <button
                        type="button"
                        onClick={() => setPEffectMode('otros')}
                        className={`btn ${pEffectMode === 'otros' ? 'btn-primary' : ''}`}
                        style={{ padding: '6px 10px', fontSize: '12px' }}
                      >
                        📝 Otros (Efecto No Numérico)
                      </button>
                    </div>

                    {/* Modo 1: Porcentajes */}
                    {pEffectMode === 'percentage' && (
                      <div>
                        <label style={{ display: 'block', fontSize: '12px', fontWeight: 'bold', marginBottom: '4px' }}>
                          Variante de Porcentaje (% sobre Saldo Disponible):
                        </label>
                        <select
                          value={selectedPVariant}
                          onChange={(e) => setSelectedPVariant(e.target.value)}
                          style={{ padding: '8px', border: '1px solid var(--ink)', width: '100%', background: '#fff', marginBottom: '8px' }}
                        >
                          <option value="var_100_60">+100% acierto / -60% error (Estándar)</option>
                          <option value="var_50_30">+50% acierto / -30% error (Medio)</option>
                          <option value="var_30_35">+30% acierto / -35% error (Moderado)</option>
                          <option value="casilla_2_reto">Casilla 2: Acierto habilita Reto E / Error -25%</option>
                          <option value="custom">Porcentajes Personalizados...</option>
                        </select>

                        {selectedPVariant === 'custom' && (
                          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginTop: '6px' }}>
                            <div>
                              <label style={{ fontSize: '11px', fontWeight: 'bold' }}>% Ganancia al Acertar:</label>
                              <input
                                type="number"
                                min={0}
                                max={500}
                                value={pCustomGainPct}
                                onChange={(e) => setPCustomGainPct(Number(e.target.value))}
                                style={{ width: '100%', padding: '6px', border: '1px solid var(--ink)' }}
                              />
                            </div>
                            <div>
                              <label style={{ fontSize: '11px', fontWeight: 'bold' }}>% Pérdida al Errar:</label>
                              <input
                                type="number"
                                min={0}
                                max={100}
                                value={pCustomLossPct}
                                onChange={(e) => setPCustomLossPct(Number(e.target.value))}
                                style={{ width: '100%', padding: '6px', border: '1px solid var(--ink)' }}
                              />
                            </div>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Modo 2: Montos Fijos en TDL */}
                    {pEffectMode === 'fixed' && (
                      <div>
                        <label style={{ display: 'block', fontSize: '12px', fontWeight: 'bold', marginBottom: '4px' }}>
                          Montos Específicos en TDL:
                        </label>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                          <div>
                            <label style={{ fontSize: '11px', fontWeight: 'bold', color: 'var(--green)' }}>Premio al Acertar (TDL):</label>
                            <input
                              type="number"
                              min={0}
                              step={100}
                              value={pFixedGainTDL}
                              onChange={(e) => setPFixedGainTDL(Number(e.target.value))}
                              style={{ width: '100%', padding: '6px', border: '1px solid var(--ink)' }}
                            />
                          </div>
                          <div>
                            <label style={{ fontSize: '11px', fontWeight: 'bold', color: 'var(--red)' }}>Descuento al Errar (TDL):</label>
                            <input
                              type="number"
                              min={0}
                              step={100}
                              value={pFixedLossTDL}
                              onChange={(e) => setPFixedLossTDL(Number(e.target.value))}
                              style={{ width: '100%', padding: '6px', border: '1px solid var(--ink)' }}
                            />
                          </div>
                        </div>
                        <div style={{ display: 'flex', gap: '6px', marginTop: '8px' }}>
                          <button
                            type="button"
                            className="btn"
                            style={{ fontSize: '11px', padding: '2px 6px' }}
                            onClick={() => { setPFixedGainTDL(3000); setPFixedLossTDL(1500); }}
                          >
                            +3.000 / -1.500 TDL
                          </button>
                          <button
                            type="button"
                            className="btn"
                            style={{ fontSize: '11px', padding: '2px 6px' }}
                            onClick={() => { setPFixedGainTDL(1000); setPFixedLossTDL(500); }}
                          >
                            +1.000 / -500 TDL
                          </button>
                          <button
                            type="button"
                            className="btn"
                            style={{ fontSize: '11px', padding: '2px 6px' }}
                            onClick={() => { setPFixedGainTDL(2000); setPFixedLossTDL(1000); }}
                          >
                            +2.000 / -1.000 TDL
                          </button>
                        </div>
                      </div>
                    )}

                    {/* Modo 3: Otros con descripción obligatoria */}
                    {pEffectMode === 'otros' && (
                      <div>
                        <label style={{ display: 'block', fontSize: '12px', fontWeight: 'bold', marginBottom: '4px', color: '#1e3a8a' }}>
                          Descripción Obligatoria del Efecto (para Auditoría):
                        </label>
                        <input
                          type="text"
                          value={pOtherDescription}
                          onChange={(e) => setPOtherDescription(e.target.value)}
                          placeholder="Ej: Avanza 2 casillas y cobra bono / Pierde el próximo turno..."
                          style={{ width: '100%', padding: '8px', border: '2px solid var(--blue)', borderRadius: '4px', fontSize: '13px' }}
                          required
                        />
                        <small style={{ display: 'block', color: '#556b62', marginTop: '4px', fontSize: '11px' }}>
                          Esta descripción se registrará en el libro de auditoría y en el PDF oficial sin afectar saldos monetarios.
                        </small>
                      </div>
                    )}
                  </div>

                  <div style={{ display: 'flex', gap: '12px', marginTop: '16px', flexWrap: 'wrap' }}>
                    <button onClick={() => handleValidateP(true)} className="btn btn-green">
                      <CheckCircle2 size={16} />
                      <span>Respuesta Correcta</span>
                    </button>
                    <button onClick={() => handleValidateP(false)} className="btn btn-red">
                      <XCircle size={16} />
                      <span>Respuesta Incorrecta</span>
                    </button>
                    <button
                      type="button"
                      onClick={handleMarkActiveUnavailable}
                      className="btn"
                      style={{ background: '#fef2f2', borderColor: '#fca5a5', color: '#b91c1c' }}
                      title="Marcar como no disponible sin aplicar cambios monetarios"
                    >
                      <AlertTriangle size={16} />
                      <span>Marcar como No Disponible</span>
                    </button>
                  </div>
                </div>
              )}

              {/* Si es Reto Económico E */}
              {activeCard.deck_type === 'E' && (
                <div style={{ background: '#dcf0df', border: '2px solid var(--green)', padding: '14px', borderRadius: '4px', marginBottom: '16px' }}>
                  <div style={{ fontWeight: 'bold', color: 'var(--green)', marginBottom: '4px' }}>
                    Regla del Motor ({activeCard.engine_rule}):
                  </div>
                  <div style={{ fontSize: '14px', marginBottom: '12px' }}>{activeCard.target_description}</div>

                  {/* Parámetros específicos según la tarjeta */}
                  {['E02', 'E09', 'E12'].includes(activeCard.code) && (
                    <div style={{ marginBottom: '12px' }}>
                      <label style={{ display: 'block', fontWeight: 'bold', fontSize: '13px', marginBottom: '4px' }}>
                        Seleccionar Equipo Objetivo / Contraparte:
                      </label>
                      <select
                        value={targetTeamId}
                        onChange={(e) => setTargetTeamId(Number(e.target.value))}
                        style={{ width: '100%', padding: '8px', border: '1px solid var(--ink)' }}
                      >
                        <option value="">Seleccioná un equipo...</option>
                        {summary?.ranking.map((r) => (
                          <option key={r.account_id} value={r.account_id}>
                            {r.team_name} (Disponible: {(r.balance_available / 100).toFixed(2)} TDL)
                          </option>
                        ))}
                      </select>
                    </div>
                  )}

                  {activeCard.code === 'E04' && (
                    <div style={{ marginBottom: '12px' }}>
                      <label style={{ display: 'block', fontWeight: 'bold', fontSize: '13px', marginBottom: '4px' }}>
                        3 Dados (Suma &le; 6 pierde 20% / Suma &gt; 6 gana 30%):
                      </label>
                      <div style={{ display: 'flex', gap: '8px' }}>
                        {[0, 1, 2].map((idx) => (
                          <input
                            key={idx}
                            type="number"
                            min={1}
                            max={6}
                            value={eDiceRolls[idx]}
                            onChange={(e) => {
                              const copy = [...eDiceRolls];
                              copy[idx] = Number(e.target.value);
                              setEDiceRolls(copy);
                            }}
                            style={{ width: '60px', padding: '8px', textAlign: 'center', border: '1px solid var(--ink)' }}
                          />
                        ))}
                        <span style={{ alignSelf: 'center', fontWeight: 'bold' }}>
                          Suma = {eDiceRolls.reduce((a, b) => a + b, 0)}
                        </span>
                      </div>
                    </div>
                  )}

                  {activeCard.code === 'E11' && (
                    <div style={{ marginBottom: '12px' }}>
                      <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 'bold', fontSize: '14px' }}>
                        <input
                          type="checkbox"
                          checked={acceptInsurance}
                          onChange={(e) => setAcceptInsurance(e.target.checked)}
                        />
                        <span>Acepta contratar Seguro del Negocio (paga 5% prima)</span>
                      </label>
                    </div>
                  )}

                  {activeCard.code === 'E15' && (
                    <div style={{ marginBottom: '12px' }}>
                      <label style={{ display: 'block', fontWeight: 'bold', fontSize: '13px', marginBottom: '4px' }}>
                        Dado (Par +20% / Impar -10%):
                      </label>
                      <input
                        type="number"
                        min={1}
                        max={6}
                        value={eDiceRolls[0]}
                        onChange={(e) => setEDiceRolls([Number(e.target.value)])}
                        style={{ width: '80px', padding: '8px', textAlign: 'center', border: '1px solid var(--ink)', fontWeight: 'bold' }}
                      />
                    </div>
                  )}

                  <div style={{ display: 'flex', gap: '10px', marginTop: '14px', flexWrap: 'wrap' }}>
                    <button onClick={handleExecuteE} className="btn btn-green" style={{ flex: 1, minWidth: '220px', justifyContent: 'center' }}>
                      <Play size={16} />
                      <span>Aplicar Efecto Atómico de {activeCard.code}</span>
                    </button>
                    <button
                      type="button"
                      onClick={handleMarkActiveUnavailable}
                      className="btn"
                      style={{ background: '#fef2f2', borderColor: '#fca5a5', color: '#b91c1c' }}
                      title="Marcar como no disponible sin aplicar efecto financiero"
                    >
                      <AlertTriangle size={16} />
                      <span>Marcar como No Disponible</span>
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Ranking de Equipos */}
      <div className="workspace">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
          <h3 style={{ fontFamily: 'Georgia, serif', fontSize: '22px' }}>
            Ranking Oficial de Equipos (Disponible + Reservado)
          </h3>
          <span style={{ fontSize: '13px', color: '#526356' }}>
            Empates en el mismo puesto · Orden visual estable
          </span>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table className="table-audacity">
            <thead>
              <tr>
                <th style={{ width: '60px', textAlign: 'center' }}>Puesto</th>
                <th>Equipo</th>
                <th style={{ textAlign: 'right' }}>Disponible</th>
                <th style={{ textAlign: 'right' }}>Reservado</th>
                <th style={{ textAlign: 'right' }}>Total (Nominal)</th>
                <th style={{ textAlign: 'center' }}>Turnos Perdidos</th>
                <th style={{ textAlign: 'center' }}>Seguro E11</th>
                <th style={{ textAlign: 'right' }}>Deudas Vencidas</th>
                <th style={{ textAlign: 'center' }}>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {summary?.ranking.map((team) => (
                <tr key={team.account_id}>
                  <td style={{ textAlign: 'center', fontWeight: 'bold', fontSize: '17px' }}>
                    #{team.rank}
                  </td>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span className="token-circle" style={{ backgroundColor: team.token_color, width: '28px', height: '28px', fontSize: '15px' }}>
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
                  <td style={{ textAlign: 'right', font: '700 16px Georgia, serif', color: 'var(--green)' }}>
                    {(team.balance_total / 100).toLocaleString('es-UY', { minimumFractionDigits: 2 })} TDL
                  </td>
                  <td style={{ textAlign: 'center' }}>
                    {team.lost_turns > 0 ? (
                      <span className="badge" style={{ background: '#fde8e8', color: '#9b1c1c' }}>
                        {team.lost_turns} turno(s)
                      </span>
                    ) : (
                      '—'
                    )}
                  </td>
                  <td style={{ textAlign: 'center' }}>
                    {team.has_insurance_e11 ? (
                      <span className="badge" style={{ background: '#def7ec', color: '#03543f' }}>
                        <ShieldCheck size={12} style={{ display: 'inline', verticalAlign: 'middle' }} /> Activo
                      </span>
                    ) : (
                      '—'
                    )}
                  </td>
                  <td style={{ textAlign: 'right', color: team.pending_debts > 0 ? 'var(--red)' : '#556b62', fontWeight: team.pending_debts > 0 ? 'bold' : 'normal' }}>
                    {team.pending_debts > 0 ? (team.pending_debts / 100).toFixed(2) + ' TDL' : '—'}
                  </td>
                  <td style={{ textAlign: 'center' }}>
                    <button
                      onClick={() => {
                        setSelectedTeamId(team.account_id);
                        setBankOpType('pay');
                        setShowBankModal(true);
                      }}
                      className="btn"
                      style={{ padding: '4px 8px', fontSize: '12px' }}
                    >
                      Operar
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Mazos P y E para extracción */}
      <div className="workspace">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px', flexWrap: 'wrap', gap: '10px' }}>
          <h3 style={{ fontFamily: 'Georgia, serif', fontSize: '20px', margin: 0 }}>
            Selección de Tarjetas (P01-P15 y E01-E15)
          </h3>
          <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
            <button
              type="button"
              onClick={() => setCardFilter('all')}
              className={`btn ${cardFilter === 'all' ? 'btn-primary' : ''}`}
              style={{ padding: '4px 10px', fontSize: '12px' }}
            >
              Todas (30)
            </button>
            <button
              type="button"
              onClick={() => setCardFilter('disponible')}
              className={`btn ${cardFilter === 'disponible' ? 'btn-primary' : ''}`}
              style={{ padding: '4px 10px', fontSize: '12px' }}
            >
              Disponibles ({countPAvailable + countEAvailable})
            </button>
            <button
              type="button"
              onClick={() => setCardFilter('no_disponible')}
              className={`btn ${cardFilter === 'no_disponible' ? 'btn-primary' : ''}`}
              style={{ padding: '4px 10px', fontSize: '12px' }}
            >
              No Disponibles ({30 - countPAvailable - countEAvailable})
            </button>
          </div>
        </div>

        <div className="decks-grid">
          <div
            className="deck-banner"
            onClick={() => handleDrawCard('P')}
            title="Extraer una tarjeta de Preguntas al azar"
          >
            <div>
              <strong>Preguntas (P)</strong>
              <small>Conceptos de economía</small>
            </div>
            <b>{countPAvailable} / 15</b>
          </div>

          <div
            className="deck-banner economic"
            onClick={() => handleDrawCard('E')}
            title="Extraer un Reto Económico al azar"
          >
            <div>
              <strong>Retos Económicos (E)</strong>
              <small>Saldos, decisiones y compromisos</small>
            </div>
            <b>{countEAvailable} / 15</b>
          </div>
        </div>

        {/* Tarjetas P y E listadas */}
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
              return (
                <div
                  key={c.code}
                  onClick={() => handleCardItemClick(c)}
                  className={`card-item ${c.deck_type === 'E' ? 'economic' : ''} ${isUsed ? 'used' : ''}`}
                  style={{ cursor: 'pointer' }}
                  title={isUsed ? `${c.code}: Ya no disponible. Clic para ver o reactivar` : `${c.code}: Disponible. Clic para seleccionar / jugar`}
                >
                  <div className="stripe"></div>
                  <strong>{c.code}</strong>
                  <small>{c.title}</small>
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

      {/* Feed de Auditoría en Tiempo Real y Exportación CSV */}
      <div className="workspace">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px', flexWrap: 'wrap', gap: '10px' }}>
          <h3 style={{ fontFamily: 'Georgia, serif', fontSize: '20px' }}>
            Auditoría en Tiempo Real de Transacciones
          </h3>
          <a
            href={`/api/games/${gameCode}/export-csv`}
            target="_blank"
            rel="noreferrer"
            className="btn btn-gold"
            style={{ textDecoration: 'none' }}
          >
            <Download size={15} />
            <span>Exportar CSV Seguro</span>
          </a>
        </div>

        <div style={{ maxHeight: '360px', overflowY: 'auto' }}>
          <table className="table-audacity" style={{ fontSize: '13px' }}>
            <thead>
              <tr>
                <th>Hora</th>
                <th>Operación</th>
                <th>Motivo</th>
                <th style={{ textAlign: 'right' }}>Monto</th>
                <th style={{ textAlign: 'center' }}>Acción</th>
              </tr>
            </thead>
            <tbody>
              {feed.map((entry) => (
                <tr key={entry.id} style={{ opacity: entry.is_reverted ? 0.45 : 1 }}>
                  <td>{entry.timestamp}</td>
                  <td>
                    <span className="badge" style={{ backgroundColor: '#fffdf5' }}>
                      {entry.operation_type}
                    </span>
                  </td>
                  <td>
                    {entry.reason} {entry.is_reverted && <strong style={{ color: 'var(--red)' }}>(REVERTIDO)</strong>}
                  </td>
                  <td style={{ textAlign: 'right', fontWeight: 'bold' }}>
                    {entry.amount_tdl} TDL
                  </td>
                  <td style={{ textAlign: 'center' }}>
                    {!entry.is_reverted && (
                      <button
                        onClick={() => handleUndo(entry.id)}
                        className="btn"
                        style={{ padding: '2px 6px', fontSize: '11px' }}
                        title="Deshacer asiento y estado asociado"
                      >
                        Deshacer
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal: Creación de Partida */}
      {showCreateModal && (
        <div className="modal-backdrop">
          <div className="modal-card" style={{ maxWidth: '520px' }}>
            <h3 style={{ font: '700 24px Georgia, serif', marginBottom: '16px' }}>Nueva Partida Audacity</h3>
            <form onSubmit={handleCreateGame} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div>
                <label style={{ fontWeight: 'bold', fontSize: '13px', display: 'block', marginBottom: '4px' }}>
                  Nombre de la Partida / Grupo:
                </label>
                <input
                  type="text"
                  value={newGameName}
                  onChange={(e) => setNewGameName(e.target.value)}
                  required
                  style={{ width: '100%', padding: '8px', border: '2px solid var(--ink)' }}
                />
              </div>

              <div>
                <label style={{ fontWeight: 'bold', fontSize: '13px', display: 'block', marginBottom: '4px' }}>
                  Perfil de Tablero y Fichas:
                </label>
                <select
                  value={newGameProfile}
                  onChange={(e) => setNewGameProfile(e.target.value as any)}
                  style={{ width: '100%', padding: '8px', border: '2px solid var(--ink)', background: '#fffdf5' }}
                >
                  <option value="genially">Genially (5 Equipos: Gallo, León, Perro, Mano, Estrella)</option>
                  <option value="prezi">Prezi (4 Equipos: Diamante, Auto, Sombrero, Cerdo)</option>
                </select>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div>
                  <label style={{ fontWeight: 'bold', fontSize: '13px', display: 'block', marginBottom: '4px' }}>
                    Saldo Inicial por Equipo (TDL):
                  </label>
                  <input
                    type="number"
                    value={initialTeamTDL}
                    onChange={(e) => setInitialTeamTDL(Number(e.target.value))}
                    style={{ width: '100%', padding: '8px', border: '2px solid var(--ink)' }}
                  />
                </div>
                <div>
                  <label style={{ fontWeight: 'bold', fontSize: '13px', display: 'block', marginBottom: '4px' }}>
                    Fondo Inicial Banco (TDL):
                  </label>
                  <input
                    type="number"
                    value={initialBankTDL}
                    onChange={(e) => setInitialBankTDL(Number(e.target.value))}
                    style={{ width: '100%', padding: '8px', border: '2px solid var(--ink)' }}
                  />
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '14px' }}>
                {gameCode && (
                  <button type="button" onClick={() => setShowCreateModal(false)} className="btn">
                    Cancelar
                  </button>
                )}
                <button type="submit" className="btn btn-primary">
                  Crear Partida y Generar Credenciales
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Credenciales de Equipos de un solo uso */}
      {createdCredentials && (
        <div className="modal-backdrop">
          <div className="modal-card" style={{ maxWidth: '640px' }}>
            <h3 style={{ font: '700 24px Georgia, serif', marginBottom: '6px' }}>Hoja de Credenciales de Equipos</h3>
            <p style={{ fontSize: '14px', color: '#556b62', marginBottom: '16px' }}>
              Entregá estas contraseñas únicas de 14 caracteres a cada equipo. Nunca se muestran en proyección.
            </p>

            <table className="table-audacity" style={{ fontSize: '13px' }}>
              <thead>
                <tr>
                  <th>Ficha</th>
                  <th>Equipo</th>
                  <th>Usuario</th>
                  <th>Contraseña Única</th>
                </tr>
              </thead>
              <tbody>
                {createdCredentials.map((c) => (
                  <tr key={c.username}>
                    <td style={{ textAlign: 'center' }}>
                      <span className="token-circle" style={{ backgroundColor: c.token_color, width: '28px', height: '28px', fontSize: '15px' }}>
                        {c.token_symbol}
                      </span>
                    </td>
                    <td><strong>{c.display_name}</strong></td>
                    <td><code>{c.username}</code></td>
                    <td><code style={{ background: '#fff', padding: '3px 6px', border: '1px solid #c0d0c4', fontWeight: 'bold' }}>{c.password}</code></td>
                  </tr>
                ))}
              </tbody>
            </table>

            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '16px' }}>
              <button onClick={() => setCreatedCredentials(null)} className="btn btn-primary">
                Entendido / Cerrar Hoja
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal: Operaciones Bancarias (Pagar, Cobrar, Transferir, Ajustar, Poner en cero) */}
      {showBankModal && (
        <div className="modal-backdrop">
          <div className="modal-card" style={{ maxWidth: '540px' }}>
            <h3 style={{ font: '700 24px Georgia, serif', marginBottom: '14px' }}>Operaciones Bancarias</h3>

            <div style={{ display: 'flex', gap: '8px', marginBottom: '16px', flexWrap: 'wrap' }}>
              {(['pay', 'collect', 'transfer', 'adjust', 'zero'] as const).map((op) => (
                <button
                  key={op}
                  type="button"
                  onClick={() => setBankOpType(op)}
                  className={`btn ${bankOpType === op ? 'btn-primary' : ''}`}
                  style={{ padding: '6px 10px', fontSize: '13px' }}
                >
                  {op === 'pay' && 'Pagar'}
                  {op === 'collect' && 'Cobrar'}
                  {op === 'transfer' && 'Transferir'}
                  {op === 'adjust' && 'Ajustar Saldo'}
                  {op === 'zero' && 'Poner a Cero'}
                </button>
              ))}
            </div>

            <form onSubmit={handleBankSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div>
                <label style={{ fontWeight: 'bold', fontSize: '13px', display: 'block', marginBottom: '4px' }}>
                  {bankOpType === 'transfer' ? 'Cuenta Origen:' : 'Equipo Involucrado:'}
                </label>
                <select
                  value={selectedTeamId}
                  onChange={(e) => setSelectedTeamId(Number(e.target.value))}
                  required
                  style={{ width: '100%', padding: '8px', border: '2px solid var(--ink)' }}
                >
                  <option value="">Seleccionar cuenta...</option>
                  {summary?.ranking.map((r) => (
                    <option key={r.account_id} value={r.account_id}>
                      {r.team_name} (Disp: {(r.balance_available / 100).toFixed(2)} TDL)
                    </option>
                  ))}
                  {bankOpType === 'adjust' && (
                    <option value={summary?.bank_account_id}>BANCO CENTRAL (Fondo Propio)</option>
                  )}
                </select>
              </div>

              {bankOpType === 'transfer' && (
                <div>
                  <label style={{ fontWeight: 'bold', fontSize: '13px', display: 'block', marginBottom: '4px' }}>
                    Cuenta Destino:
                  </label>
                  <select
                    value={destTeamId}
                    onChange={(e) => setDestTeamId(Number(e.target.value))}
                    required
                    style={{ width: '100%', padding: '8px', border: '2px solid var(--ink)' }}
                  >
                    <option value="">Seleccionar cuenta destino...</option>
                    {summary?.ranking.map((r) => (
                      <option key={r.account_id} value={r.account_id}>
                        {r.team_name}
                      </option>
                    ))}
                  </select>
                </div>
              )}

              {bankOpType !== 'adjust' && bankOpType !== 'zero' && (
                <div>
                  <label style={{ fontWeight: 'bold', fontSize: '13px', display: 'block', marginBottom: '4px' }}>
                    Monto (TDL):
                  </label>
                  <input
                    type="number"
                    min={0.01}
                    step={0.01}
                    value={opAmountTDL}
                    onChange={(e) => setOpAmountTDL(Number(e.target.value))}
                    required
                    style={{ width: '100%', padding: '8px', border: '2px solid var(--ink)' }}
                  />
                </div>
              )}

              {bankOpType === 'adjust' && (
                <div>
                  <label style={{ fontWeight: 'bold', fontSize: '13px', display: 'block', marginBottom: '4px' }}>
                    Saldo Objetivo Disponible (TDL):
                  </label>
                  <input
                    type="number"
                    min={0}
                    step={0.01}
                    value={targetAdjustTDL}
                    onChange={(e) => setTargetAdjustTDL(Number(e.target.value))}
                    required
                    style={{ width: '100%', padding: '8px', border: '2px solid var(--ink)' }}
                  />
                  <small style={{ color: '#556b62' }}>La diferencia se liquidará contra la cuenta de ajustes del sistema.</small>
                </div>
              )}

              {bankOpType === 'zero' && (
                <div>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px', color: 'var(--red)', fontWeight: 'bold' }}>
                    <input
                      type="checkbox"
                      checked={resolveContracts}
                      onChange={(e) => setResolveContracts(e.target.checked)}
                    />
                    <span>Confirmo resolución explícita de contratos/deudas de esta cuenta</span>
                  </label>
                </div>
              )}

              <div>
                <label style={{ fontWeight: 'bold', fontSize: '13px', display: 'block', marginBottom: '4px' }}>
                  Motivo Obligatorio de Auditoría:
                </label>
                <input
                  type="text"
                  value={opReason}
                  onChange={(e) => setOpReason(e.target.value)}
                  placeholder="Ej. Premio especial, corrección de tirada..."
                  required
                  style={{ width: '100%', padding: '8px', border: '2px solid var(--ink)' }}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '10px' }}>
                <button type="button" onClick={() => setShowBankModal(false)} className="btn">
                  Cancelar
                </button>
                <button type="submit" className="btn btn-primary">
                  Confirmar Operación
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Claves Docente P01-P15 */}
      {showAdminPModal && (
        <div className="modal-backdrop">
          <div className="modal-card" style={{ maxWidth: '800px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
              <h3 style={{ font: '700 24px Georgia, serif', color: 'var(--blue)' }}>
                Catálogo de Preguntas P01-P15 (Claves Docente Protegidas)
              </h3>
              <button onClick={() => setShowAdminPModal(false)} className="btn">
                Cerrar
              </button>
            </div>

            <div style={{ maxHeight: '65vh', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {adminPDeck.map((p) => (
                <div key={p.code} style={{ background: '#fff', border: '1px solid #c0d0c4', padding: '12px', borderRadius: '4px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                    <span className="badge" style={{ backgroundColor: 'var(--blue)', color: '#fff' }}>
                      {p.code}: {p.title}
                    </span>
                    <span style={{ fontSize: '12px', color: '#556b62' }}>{p.source}</span>
                  </div>
                  <p style={{ fontSize: '14px', marginBottom: '8px' }}>{p.text}</p>
                  <div style={{ background: '#f5fbf7', borderLeft: '4px solid var(--green)', padding: '6px 10px', fontSize: '13px' }}>
                    <strong>Respuesta aceptable del Banco:</strong> {p.teacher_answer}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Modal: Fin de Partida */}
      {showEndGameModal && (
        <div className="modal-backdrop">
          <div className="modal-card" style={{ maxWidth: '520px', border: '3px solid #dc2626' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '14px', color: '#dc2626' }}>
              <Flag size={28} />
              <h3 style={{ font: '700 24px Georgia, serif', margin: 0 }}>
                ¿Finalizar Partida de Audacity?
              </h3>
            </div>
            <p style={{ fontSize: '15px', color: '#334155', lineHeight: 1.6, marginBottom: '16px' }}>
              Al confirmar el <strong>FIN DE PARTIDA</strong>:
            </p>
            <ul style={{ fontSize: '14px', color: '#475569', marginBottom: '20px', paddingLeft: '20px', lineHeight: 1.6 }}>
              <li>Se cerrará oficialmente el juego y se congelará el tablero.</li>
              <li>No se podrán avanzar más turnos ni realizar más transferencias o cobros.</li>
              <li>Se fijará el podio y las posiciones finales de todos los equipos.</li>
              <li>Podrás descargar de inmediato el <strong>informe oficial de auditoría en PDF</strong>.</li>
            </ul>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
              <button
                type="button"
                onClick={() => setShowEndGameModal(false)}
                disabled={endingGame}
                className="btn"
              >
                Continuar Jugando
              </button>
              <button
                type="button"
                onClick={handleEndGame}
                disabled={endingGame}
                className="btn btn-red"
                style={{ background: '#dc2626', color: '#fff', fontWeight: 'bold' }}
              >
                {endingGame ? 'Cerrando Partida...' : 'Confirmar Fin de Partida'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal: Limpiar Base de Datos */}
      {showCleanDbModal && (
        <div className="modal-backdrop">
          <div className="modal-card" style={{ maxWidth: '520px', border: '3px solid #b91c1c' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '14px', color: '#b91c1c' }}>
              <AlertTriangle size={30} />
              <h3 style={{ font: '700 24px Georgia, serif', margin: 0 }}>
                ¿Limpiar y Vaciar Base de Datos?
              </h3>
            </div>
            <p style={{ fontSize: '14px', color: '#334155', lineHeight: 1.5, marginBottom: '12px' }}>
              Esta acción es <strong>definitiva e irreversible</strong>. Se eliminarán de forma permanente:
            </p>
            <ul style={{ fontSize: '13.5px', color: '#475569', marginBottom: '16px', paddingLeft: '20px', lineHeight: 1.6 }}>
              <li>Todas las partidas creadas en el sistema.</li>
              <li>Todas las cuentas bancarias, saldos acumulados y libros diarios.</li>
              <li>Todos los contratos de deuda y amortizaciones.</li>
              <li>Todas las tarjetas jugadas y turnos registrados.</li>
              <li>Todos los usuarios contadores de equipos.</li>
            </ul>
            <div style={{ background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: '6px', padding: '10px 14px', marginBottom: '20px', fontSize: '13px', color: '#166534', fontWeight: 600 }}>
              ✓ Tu usuario <code>admin_docente</code> y tu sesión activa permanecerán intactos.
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
              <button
                type="button"
                onClick={() => setShowCleanDbModal(false)}
                disabled={cleaningDb}
                className="btn"
              >
                Cancelar
              </button>
              <button
                type="button"
                onClick={handleCleanDatabase}
                disabled={cleaningDb}
                className="btn btn-red"
                style={{ background: '#b91c1c', color: '#fff', fontWeight: 'bold' }}
              >
                {cleaningDb ? 'Limpiando Base de Datos...' : 'Sí, Vaciar Base de Datos'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal: Inspeccionar / Reactivar Tarjeta No Disponible */}
      {inspectingUsedCard && (
        <div className="modal-backdrop">
          <div className="modal-card" style={{ maxWidth: '680px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
              <span
                className="badge"
                style={{
                  backgroundColor: inspectingUsedCard.deck_type === 'P' ? 'var(--blue)' : 'var(--green)',
                  color: 'white',
                  fontSize: '13px',
                }}
              >
                {inspectingUsedCard.code} · {inspectingUsedCard.deck_type === 'P' ? 'Pregunta' : 'Reto Económico'} · NO DISPONIBLE
              </span>
              <button onClick={() => setInspectingUsedCard(null)} className="btn">
                Cerrar
              </button>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: inspectingUsedCard.image_path ? 'minmax(200px, 280px) 1fr' : '1fr', gap: '16px', alignItems: 'center' }}>
              {inspectingUsedCard.image_path && (
                <div>
                  <img
                    src={inspectingUsedCard.image_path}
                    alt={inspectingUsedCard.title}
                    style={{ width: '100%', border: '2px solid var(--ink)', borderRadius: '4px' }}
                  />
                </div>
              )}
              <div>
                <h4 style={{ font: '700 22px Georgia, serif', marginBottom: '8px' }}>{inspectingUsedCard.title}</h4>
                <p style={{ fontSize: '15px', lineHeight: 1.5, color: '#334155', marginBottom: '14px' }}>
                  {inspectingUsedCard.text}
                </p>
                {inspectingUsedCard.teacher_answer && (
                  <div style={{ background: '#e1f1fb', border: '1px solid var(--blue)', padding: '10px', borderRadius: '4px', marginBottom: '14px', fontSize: '13px' }}>
                    <strong>Clave Docente:</strong> {inspectingUsedCard.teacher_answer}
                  </div>
                )}
                <div style={{ padding: '8px 12px', background: '#fee2e2', borderRadius: '4px', color: '#991b1b', fontSize: '13px', fontWeight: 'bold', marginBottom: '14px' }}>
                  Estado actual: NO DISPONIBLE (Visible para los equipos contadores)
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '16px', borderTop: '1px solid #c0d0c4', paddingTop: '12px' }}>
              <button
                type="button"
                onClick={() => setInspectingUsedCard(null)}
                className="btn"
              >
                Volver
              </button>
              <button
                type="button"
                onClick={() => handleReactivateCard(inspectingUsedCard.code)}
                className="btn btn-primary"
                title="Volver a poner esta tarjeta en el mazo como DISPONIBLE"
              >
                <RotateCcw size={15} />
                <span>Reactivar (Marcar como DISPONIBLE)</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
