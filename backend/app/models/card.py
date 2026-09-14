from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database import Base

class Card(Base):
    __tablename__ = "cards"

    code = Column(String(10), primary_key=True)  # "P01" .. "P15", "E01" .. "E15"
    deck_type = Column(String(5), nullable=False, index=True)  # "P" or "E"
    title = Column(String(100), nullable=False)
    text = Column(Text, nullable=False)
    
    # Strictly confidential for teacher/bank
    teacher_answer = Column(Text, nullable=True)
    source = Column(String(200), nullable=True)
    
    # Motor de reglas spec
    engine_rule = Column(String(100), nullable=True)
    target_description = Column(String(200), nullable=True)
    image_path = Column(String(200), nullable=False)

    instances = relationship("CardInstance", back_populates="card")

class CardInstance(Base):
    __tablename__ = "card_instances"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id", ondelete="CASCADE"), nullable=False, index=True)
    card_code = Column(String(10), ForeignKey("cards.code", ondelete="RESTRICT"), nullable=False, index=True)
    
    status = Column(String(20), default="disponible", nullable=False, index=True)  # "disponible", "asignada", "resuelta_usada", "devuelta"
    assigned_to_account_id = Column(Integer, ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True)
    
    assigned_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    execution_result = Column(JSON, default=dict)
    
    # Relationships
    game = relationship("Game", back_populates="card_instances")
    card = relationship("Card", back_populates="instances")
    assigned_account = relationship("Account")
