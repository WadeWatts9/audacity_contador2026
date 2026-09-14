from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, BigInteger, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database import Base

class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    account_type = Column(String(30), nullable=False)  # "banco", "equipo", "ajustes_emision"
    account_name = Column(String(100), nullable=False)
    
    # Financial balances in integer cents (TDL * 100)
    # Total = balance_available + balance_reserved
    balance_available = Column(BigInteger, default=0, nullable=False)
    balance_reserved = Column(BigInteger, default=0, nullable=False)
    
    # Game status
    lost_turns = Column(Integer, default=0, nullable=False)
    has_insurance_e11 = Column(Boolean, default=False, nullable=False)  # Póliza E11 activa
    is_closed = Column(Boolean, default=False, nullable=False)          # Cuenta cerrada / bloqueada
    
    # Sequential opportunities/turns had by this team
    turn_opportunities_count = Column(Integer, default=0, nullable=False)

    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    game = relationship("Game", back_populates="accounts")
    user = relationship("User", back_populates="accounts")
    
    @property
    def balance_total(self) -> int:
        return self.balance_available + self.balance_reserved
