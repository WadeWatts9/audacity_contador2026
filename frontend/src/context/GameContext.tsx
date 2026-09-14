import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { GameSummary, AuditEntry, Card } from '../types';
import { api, createAudacityWebSocket } from '../api/client';

interface GameContextType {
  gameCode: string;
  setGameCode: (code: string) => void;
  summary: GameSummary | null;
  feed: AuditEntry[];
  pDeck: Card[];
  eDeck: Card[];
  countPAvailable: number;
  countEAvailable: number;
  loading: boolean;
  refreshGame: () => Promise<void>;
  notification: string | null;
  setNotification: (msg: string | null) => void;
}

const GameContext = createContext<GameContextType | undefined>(undefined);

export const GameProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [gameCode, setGameCodeState] = useState<string>(() => {
    return localStorage.getItem('audacity_active_game') || '';
  });
  const [summary, setSummary] = useState<GameSummary | null>(null);
  const [feed, setFeed] = useState<AuditEntry[]>([]);
  const [pDeck, setPDeck] = useState<Card[]>([]);
  const [eDeck, setEDeck] = useState<Card[]>([]);
  const [countPAvailable, setCountPAvailable] = useState<number>(15);
  const [countEAvailable, setCountEAvailable] = useState<number>(15);
  const [loading, setLoading] = useState<boolean>(false);
  const [notification, setNotification] = useState<string | null>(null);

  const setGameCode = (code: string) => {
    const clean = code.toUpperCase().trim();
    setGameCodeState(clean);
    if (clean) {
      localStorage.setItem('audacity_active_game', clean);
    } else {
      localStorage.removeItem('audacity_active_game');
    }
  };

  const refreshGame = useCallback(async () => {
    if (!gameCode) return;
    try {
      setLoading(true);
      const [sum, fd, decks] = await Promise.all([
        api.getGameSummary(gameCode),
        api.getGameFeed(gameCode),
        api.getDecks(gameCode),
      ]);
      setSummary(sum);
      setFeed(fd);
      setPDeck(decks.p_deck);
      setEDeck(decks.e_deck);
      setCountPAvailable(decks.count_p_available);
      setCountEAvailable(decks.count_e_available);
    } catch (err: any) {
      console.error('Error refreshing game:', err);
    } finally {
      setLoading(false);
    }
  }, [gameCode]);

  useEffect(() => {
    if (!gameCode) {
      setSummary(null);
      return;
    }
    refreshGame();

    // Conectar WebSocket para sincronización inmediata (<2s)
    const ws = createAudacityWebSocket(gameCode, (payload) => {
      // Al recibir cualquier evento del juego, refrescar estado canónico
      refreshGame();
      if (payload.data?.message) {
        setNotification(payload.data.message);
      } else if (payload.event === 'BALANCE_UPDATE' && payload.data?.reason) {
        setNotification(`Transacción: ${payload.data.reason}`);
      } else if (payload.event === 'TURN_ADVANCED') {
        setNotification(`Turno de ${payload.data.team_name}`);
      }
    });

    return () => {
      ws.close();
    };
  }, [gameCode, refreshGame]);

  return (
    <GameContext.Provider
      value={{
        gameCode,
        setGameCode,
        summary,
        feed,
        pDeck,
        eDeck,
        countPAvailable,
        countEAvailable,
        loading,
        refreshGame,
        notification,
        setNotification,
      }}
    >
      {children}
    </GameContext.Provider>
  );
};

export const useGame = () => {
  const context = useContext(GameContext);
  if (!context) {
    throw new Error('useGame debe ser usado dentro de un GameProvider');
  }
  return context;
};
