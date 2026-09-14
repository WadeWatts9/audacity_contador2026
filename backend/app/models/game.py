from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, BigInteger, JSON
from sqlalchemy.orm import relationship
from app.database import Base

class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    profile = Column(String(20), default="genially")  # "genially" (5 fichas) o "prezi" (4 fichas)
    status = Column(String(20), default="configuracion")  # "configuracion", "activa", "pausada", "finalizada"
    
    # Financial parameters in cents (e.g. 10.000 TDL = 1.000.000 centésimos)
    initial_team_balance = Column(BigInteger, default=1000000)
    initial_bank_balance = Column(BigInteger, default=10000000)
    
    # Turn tracking
    current_turn_number = Column(Integer, default=1)
    current_team_order_index = Column(Integer, default=0)
    turn_order = Column(JSON, default=list)  # List of account_ids in play order
    
    # Rules configuration (preset adjustments, base calculation, etc.)
    rules_config = Column(JSON, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    closed_at = Column(DateTime, nullable=True)

    # Relationships
    accounts = relationship("Account", back_populates="game", cascade="all, delete-orphan")
    ledger_entries = relationship("LedgerEntry", back_populates="game", cascade="all, delete-orphan")
    card_instances = relationship("CardInstance", back_populates="game", cascade="all, delete-orphan")
    contracts = relationship("Contract", back_populates="game", cascade="all, delete-orphan")
    turn_records = relationship("TurnRecord", back_populates="game", cascade="all, delete-orphan")
