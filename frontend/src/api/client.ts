import { GameSummary, BoardSquare, Card, AuditEntry, MyTeamStatus } from '../types';

const API_BASE = '/api';

export function getAuthToken(): string | null {
  return localStorage.getItem('audacity_token');
}

export function setAuthToken(token: string) {
  localStorage.setItem('audacity_token', token);
}

export function removeAuthToken() {
  localStorage.removeItem('audacity_token');
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = getAuthToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorDetail = 'Error en la solicitud';
    try {
      const errJson = await response.json();
      errorDetail = errJson.detail || errorDetail;
    } catch {
      // Ignorar parse error
    }
    throw new Error(errorDetail);
  }

  return response.json();
}

export const api = {
  // Auth
  login: (data: { username: string; password: string; game_code?: string }) =>
    request<{ access_token: string; token_type: string; user: any }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  getMe: () => request<any>('/auth/me'),

  // Games
  createGame: (data: {
    name: string;
    profile: string;
    initial_team_balance: number;
    initial_bank_balance: number;
    rules_config?: Record<string, any>;
  }) => request<any>('/games', { method: 'POST', body: JSON.stringify(data) }),

  getGameSummary: (code: string) => request<GameSummary>(`/games/${code}`),

  getGameFeed: (code: string, limit: number = 50) =>
    request<AuditEntry[]>(`/games/${code}/feed?limit=${limit}`),

  endGame: (code: string) => request<any>(`/games/${code}/end-game`, { method: 'POST' }),

  cleanDatabase: () => request<{ status: string; message: string }>('/games/admin/clean-database', { method: 'POST' }),

  getExportPdfUrl: (code: string) => `${API_BASE}/games/${code}/export-pdf`,

  // Bank
  payToTeam: (data: { team_account_id: number; amount_cents: number; reason: string }) =>
    request<any>('/bank/pay', { method: 'POST', body: JSON.stringify(data) }),

  collectFromTeam: (data: { team_account_id: number; amount_cents: number; reason: string }) =>
    request<any>('/bank/collect', { method: 'POST', body: JSON.stringify(data) }),

  transfer: (data: { source_account_id: number; destination_account_id: number; amount_cents: number; reason: string }) =>
    request<any>('/bank/transfer', { method: 'POST', body: JSON.stringify(data) }),

  adjustBalance: (data: { account_id: number; target_available_cents: number; reason: string }) =>
    request<any>('/bank/adjust', { method: 'POST', body: JSON.stringify(data) }),

  setZero: (data: { account_id: number; reason: string; resolve_contracts_explicitly?: boolean }) =>
    request<any>('/bank/set-zero', { method: 'POST', body: JSON.stringify(data) }),

  undoTransaction: (data: { entry_id: number; reason?: string }) =>
    request<any>('/bank/undo', { method: 'POST', body: JSON.stringify(data) }),

  // Turns
  getBoardSquares: () => request<BoardSquare[]>('/turns/squares'),

  advanceTurn: (code: string, data: { dice_roll?: number; square_id?: number; notes?: string }) =>
    request<any>(`/turns/advance/${code}`, { method: 'POST', body: JSON.stringify(data) }),

  // Cards
  getDecks: (code: string) =>
    request<{ count_p_available: number; count_e_available: number; p_deck: Card[]; e_deck: Card[] }>(
      `/cards/decks/${code}`
    ),

  getAdminPDeck: (code: string) => request<Card[]>(`/cards/admin/deck-p/${code}`),

  drawCard: (code: string, deck_type: 'P' | 'E', card_code?: string) =>
    request<any>(`/cards/draw/${code}`, {
      method: 'POST',
      body: JSON.stringify({ deck_type, card_code }),
    }),

  validatePCard: (data: {
    instance_id: number;
    is_correct: boolean;
    variant_id?: string;
    effect_type?: 'percentage' | 'fixed' | 'otros';
    gain_pct?: number;
    loss_pct?: number;
    gain_amount_tdl?: number;
    loss_amount_tdl?: number;
    other_description?: string;
  }) => request<any>('/cards/validate-p', { method: 'POST', body: JSON.stringify(data) }),

  executeECard: (data: {
    instance_id: number;
    target_account_id?: number;
    second_target_account_id?: number;
    dice_rolls?: number[];
    accept_insurance?: boolean;
  }) => request<any>('/cards/execute-e', { method: 'POST', body: JSON.stringify(data) }),

  resetDecks: (code: string) => request<any>(`/cards/reset/${code}`, { method: 'POST' }),

  // Team
  getMyTeamStatus: () => request<MyTeamStatus>('/teams/me/status'),

  teamTransfer: (data: { destination_account_id: number; amount_cents: number; reason: string }) =>
    request<any>('/teams/transfer', { method: 'POST', body: JSON.stringify(data) }),
};

// WebSocket Helper (usa el mismo host y protocolo relativo)
export function createAudacityWebSocket(gameCode: string, onMessage: (msg: { event: string; data: any }) => void) {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${protocol}//${window.location.host}/ws/${gameCode}`;

  let ws: WebSocket | null = null;
  let isClosed = false;

  function connect() {
    ws = new WebSocket(wsUrl);

    ws.onmessage = (event) => {
      try {
        const parsed = JSON.parse(event.data);
        if (parsed.event !== 'pong') {
          onMessage(parsed);
        }
      } catch (e) {
        console.error('Error parseando WebSocket payload:', e);
      }
    };

    ws.onclose = () => {
      if (!isClosed) {
        setTimeout(connect, 2000); // Reconexión automática
      }
    };
  }

  connect();

  // Ping periódico cada 25s
  const interval = setInterval(() => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send('ping');
    }
  }, 25000);

  return {
    close: () => {
      isClosed = true;
      clearInterval(interval);
      if (ws) ws.close();
    },
  };
}
