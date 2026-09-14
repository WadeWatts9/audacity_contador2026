from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database import Base

class TurnRecord(Base):
    __tablename__ = "turn_records"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id", ondelete="CASCADE"), nullable=False, index=True)
    team_account_id = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    
    turn_number = Column(Integer, nullable=False)
    opportunity_number = Column(Integer, nullable=False)
    
    dice_roll = Column(Integer, nullable=True)  # 1 to 6
    square_number = Column(Integer, nullable=True)  # 1 to 12
    square_name = Column(String(100), nullable=True)
    
    card_code = Column(String(10), nullable=True)
    was_turn_lost = Column(Integer, default=0, nullable=False)  # 1 if the turn was skipped due to lost_turns
    
    action_summary = Column(Text, nullable=False)
    details_json = Column(JSON, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    game = relationship("Game", back_populates="turn_records")
    team_account = relationship("Account")
