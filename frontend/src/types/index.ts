export type UserRole = 'admin_docente' | 'equipo';

export interface User {
  id: number;
  username: string;
  role: UserRole;
  display_name: string;
  token_symbol?: string;
  token_color?: string;
  account_id?: number;
  game_id?: number;
  game_code?: string;
}

export interface TeamCredentials {
  username: string;
  display_name: string;
  password: string;
  token_symbol: string;
  token_color: string;
  account_id: number;
}

export interface RankingItem {
  rank: number;
  account_id: number;
  team_name: string;
  token_symbol: string;
  token_color: string;
  balance_available: number;
  balance_reserved: number;
  balance_total: number;
  lost_turns: number;
  has_insurance_e11: boolean;
  pending_debts: number;
  active_credits: number;
}

export interface Game {
  id: number;
  code: string;
  name: string;
  profile: 'genially' | 'prezi';
  status: string;
  current_turn_number: number;
  current_team_order_index: number;
  initial_team_balance: number;
  initial_bank_balance: number;
  rules_config: Record<string, any>;
  created_at: string;
  credentials_sheet?: TeamCredentials[];
}

export interface GameSummary {
  game: Game;
  bank_balance: number;
  bank_account_id: number;
  active_team_id: number | null;
  active_team_name: string | null;
  ranking: RankingItem[];
  server_time: string;
}

export interface Card {
  code: string;
  deck_type: 'P' | 'E';
  title: string;
  text: string;
  teacher_answer?: string;
  source?: string;
  engine_rule?: string;
  target_description?: string;
  image_path: string;
  status?: string;
  assigned_to?: number;
  instance_id?: number;
}

export interface BoardSquare {
  id: number;
  name: string;
  description: string;
  requires_card?: boolean;
  card_type?: 'P' | 'E';
  variants?: Array<{
    id: string;
    label: string;
    gain_pct?: number;
    loss_pct?: number;
    gain_fixed?: number;
    loss_fixed?: number;
  }>;
  enables_e_on_correct?: boolean;
  loss_pct?: number;
  loss_pct_default?: number;
  gain_pct_default?: number;
  lost_turns?: number;
  reserve_pct?: number;
  interest_pct?: number;
  extra_roll?: boolean;
}

export interface AuditEntry {
  id: number;
  transaction_id: string;
  operation_type: string;
  amount: number;
  amount_tdl: string;
  reason: string;
  source_id: number | null;
  destination_id: number | null;
  is_reverted: boolean;
  timestamp: string;
  full_timestamp: string;
}

export interface MyTeamStatus {
  account_id: number;
  team_name: string;
  symbol: string;
  color: string;
  balance_available: number;
  balance_reserved: number;
  balance_total: number;
  lost_turns: number;
  has_insurance_e11: boolean;
  is_my_turn: boolean;
  current_round: number;
  debts_count: number;
  credits_count: number;
  history: Array<{
    id: number;
    operation_type: string;
    amount: number;
    amount_tdl: string;
    direction: 'debito' | 'credito';
    reason: string;
    timestamp: string;
  }>;
  available_opponents: Array<{ id: number; name: string }>;
}
