from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class GameCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    profile: str = Field("genially", description="'genially' (5 fichas) o 'prezi' (4 fichas)")
    initial_team_balance: int = Field(1000000, description="Saldo inicial por equipo en centésimos (10.000 TDL = 1000000)")
    initial_bank_balance: int = Field(10000000, description="Saldo inicial del Banco en centésimos (100.000 TDL = 10000000)")
    rules_config: Optional[Dict[str, Any]] = Field(default_factory=dict)

class TeamCredentials(BaseModel):
    username: str
    display_name: str
    password: str
    token_symbol: str
    token_color: str
    account_id: int

class GameResponse(BaseModel):
    id: int
    code: str
    name: str
    profile: str
    status: str
    current_turn_number: int
    current_team_order_index: int
    initial_team_balance: int
    initial_bank_balance: int
    rules_config: Dict[str, Any]
    created_at: datetime
    credentials_sheet: Optional[List[TeamCredentials]] = None

    class Config:
        from_attributes = True

class RankingItem(BaseModel):
    rank: int
    account_id: int
    team_name: str
    token_symbol: str
    token_color: str
    balance_available: int
    balance_reserved: int
    balance_total: int
    lost_turns: int
    has_insurance_e11: bool
    pending_debts: int = 0
    active_credits: int = 0

class GameSummaryResponse(BaseModel):
    game: GameResponse
    bank_balance: int
    bank_account_id: int
    active_team_id: Optional[int]
    active_team_name: Optional[str]
    ranking: List[RankingItem]
    server_time: str
