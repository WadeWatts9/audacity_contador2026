from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class AdvanceTurnRequest(BaseModel):
    dice_roll: Optional[int] = Field(None, ge=1, le=6)
    square_id: Optional[int] = Field(None, ge=1, le=12)
    notes: Optional[str] = None

class TurnStateResponse(BaseModel):
    current_turn_number: int
    current_team_order_index: int
    active_team_account_id: int
    active_team_name: str
    active_team_symbol: str
    active_team_color: str
    active_team_lost_turns: int
    can_roll: bool
    last_dice_roll: Optional[int] = None
    last_square_id: Optional[int] = None
    last_square_name: Optional[str] = None
