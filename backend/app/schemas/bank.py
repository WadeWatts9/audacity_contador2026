from pydantic import BaseModel, Field
from typing import Optional

class PayToTeamRequest(BaseModel):
    team_account_id: int
    amount_cents: int = Field(..., gt=0)
    reason: str = Field(..., min_length=3, max_length=255)

class CollectFromTeamRequest(BaseModel):
    team_account_id: int
    amount_cents: int = Field(..., gt=0)
    reason: str = Field(..., min_length=3, max_length=255)

class TransferRequest(BaseModel):
    source_account_id: int
    destination_account_id: int
    amount_cents: int = Field(..., gt=0)
    reason: str = Field(..., min_length=3, max_length=255)

class AdjustBalanceRequest(BaseModel):
    account_id: int
    target_available_cents: int = Field(..., ge=0)
    reason: str = Field(..., min_length=3, max_length=255)

class SetZeroRequest(BaseModel):
    account_id: int
    reason: str = Field(..., min_length=3, max_length=255)
    resolve_contracts_explicitly: bool = Field(False, description="Confirmar resolución explícita de contratos vigentes")

class UndoRequest(BaseModel):
    entry_id: int
    reason: Optional[str] = None
