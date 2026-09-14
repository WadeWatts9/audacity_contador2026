from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class CardPublicResponse(BaseModel):
    code: str
    deck_type: str
    title: str
    text: str
    engine_rule: Optional[str] = None
    target_description: Optional[str] = None
    image_path: str

    class Config:
        from_attributes = True

class CardPrivateResponse(CardPublicResponse):
    teacher_answer: Optional[str] = None
    source: Optional[str] = None

class CardInstanceResponse(BaseModel):
    id: int
    card_code: str
    status: str
    assigned_to_account_id: Optional[int] = None
    assigned_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    card: CardPublicResponse

    class Config:
        from_attributes = True

class CardDrawRequest(BaseModel):
    deck_type: str = Field(..., pattern="^(P|E)$")
    card_code: Optional[str] = None  # Specific card or random if omitted

class CardValidatePRequest(BaseModel):
    instance_id: int
    is_correct: bool
    variant_id: Optional[str] = Field("var_100_60", description="ID de variante de casilla de pregunta")
    effect_type: Optional[str] = Field("percentage", description="Tipo de efecto: percentage, fixed, otros")
    gain_pct: Optional[float] = None
    loss_pct: Optional[float] = None
    gain_amount_tdl: Optional[float] = None
    loss_amount_tdl: Optional[float] = None
    other_description: Optional[str] = None
    custom_gain_pct: Optional[float] = None
    custom_loss_pct: Optional[float] = None
    custom_fixed_gain: Optional[int] = None
    custom_fixed_loss: Optional[int] = None

class CardExecuteERequest(BaseModel):
    instance_id: int
    target_account_id: Optional[int] = None
    second_target_account_id: Optional[int] = None  # For Casilla 12
    dice_rolls: Optional[List[int]] = None          # For E04, E15 or digital
    accept_insurance: Optional[bool] = None         # For E11
