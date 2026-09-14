from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, BigInteger, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database import Base

class LedgerEntry(Base):
    """
    Asiento contable inmutable con partida doble balanceada y auditoría completa.
    """
    __tablename__ = "ledger_entries"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String(50), index=True, nullable=False)
    game_id = Column(Integer, ForeignKey("games.id", ondelete="CASCADE"), nullable=False, index=True)
    
    source_account_id = Column(Integer, ForeignKey("accounts.id", ondelete="RESTRICT"), nullable=True, index=True)
    destination_account_id = Column(Integer, ForeignKey("accounts.id", ondelete="RESTRICT"), nullable=True, index=True)
    
    amount = Column(BigInteger, nullable=False)  # In cents
    operation_type = Column(String(50), nullable=False)  # 'pago', 'premio', 'perdida', 'transferencia', 'ajuste', 'prestamo', 'cuota', 'reserva', 'liberacion', 'reversion'
    reason = Column(String(255), nullable=False)
    rule_version = Column(String(50), default="1.0")
    idempotency_key = Column(String(100), unique=True, nullable=True, index=True)
    
    # Balances before and after
    source_available_before = Column(BigInteger, nullable=True)
    source_available_after = Column(BigInteger, nullable=True)
    source_reserved_before = Column(BigInteger, nullable=True)
    source_reserved_after = Column(BigInteger, nullable=True)

    dest_available_before = Column(BigInteger, nullable=True)
    dest_available_after = Column(BigInteger, nullable=True)
    dest_reserved_before = Column(BigInteger, nullable=True)
    dest_reserved_after = Column(BigInteger, nullable=True)

    # Actor & Approver
    actor_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approver_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Reversal tracking
    is_reverted = Column(Boolean, default=False, nullable=False)
    reverted_by_id = Column(Integer, ForeignKey("ledger_entries.id", ondelete="SET NULL"), nullable=True)
    reverts_entry_id = Column(Integer, ForeignKey("ledger_entries.id", ondelete="SET NULL"), nullable=True)
    
    # Snapshot of state associated with the transaction for full undo
    # (e.g. lost_turns_delta, contract_id, insurance_consumed, card_instance_id)
    state_snapshot = Column(JSON, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    game = relationship("Game", back_populates="ledger_entries")
    source_account = relationship("Account", foreign_keys=[source_account_id])
    destination_account = relationship("Account", foreign_keys=[destination_account_id])
    actor = relationship("User", foreign_keys=[actor_id])
    approver = relationship("User", foreign_keys=[approver_id])
