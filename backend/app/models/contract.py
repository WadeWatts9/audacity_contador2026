from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, BigInteger, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database import Base

class Contract(Base):
    """
    Contratos financieros pluriturnos: préstamos (E02, E14), ahorros/plazos fijos (E05, casillas),
    y bonificaciones diferidas (E01).
    """
    __tablename__ = "contracts"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id", ondelete="CASCADE"), nullable=False, index=True)
    
    contract_type = Column(String(50), nullable=False)  # "prestamo_e02", "prestamo_e14", "ahorro_e05", "inversion_e01", "plazo_fijo_casilla", "ahorro_casilla"
    description = Column(String(255), nullable=False)
    
    creditor_account_id = Column(Integer, ForeignKey("accounts.id", ondelete="RESTRICT"), nullable=True, index=True)
    debtor_account_id = Column(Integer, ForeignKey("accounts.id", ondelete="RESTRICT"), nullable=False, index=True)
    
    # Financial values in cents
    principal_amount = Column(BigInteger, default=0, nullable=False)
    fixed_repayment_amount = Column(BigInteger, nullable=True)  # For E14: C + 10%
    total_repaid = Column(BigInteger, default=0, nullable=False)
    
    # Turn tracking
    created_at_opportunity = Column(Integer, nullable=False)  # Debtor's opportunity number at creation
    total_installments = Column(Integer, default=1, nullable=False)
    installments_completed = Column(Integer, default=0, nullable=False)
    
    # Status: 'activo', 'ejecutado', 'vencido_impago', 'cancelado', 'revertido'
    status = Column(String(30), default="activo", nullable=False, index=True)
    
    # Metadata (e.g. original base B, interest rate, parameters)
    metadata_json = Column(JSON, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    game = relationship("Game", back_populates="contracts")
    creditor_account = relationship("Account", foreign_keys=[creditor_account_id])
    debtor_account = relationship("Account", foreign_keys=[debtor_account_id])
    scheduled_events = relationship("ScheduledEvent", back_populates="contract", cascade="all, delete-orphan")

class ScheduledEvent(Base):
    """
    Eventos programados para ejecutarse al inicio de turno de un equipo específico.
    Orden de inicio por especificación:
    1: liberar depósitos y abonar sus intereses
    2: abonar bonificaciones diferidas
    3: cobrar cuotas y deudas por fecha de creación (desempate por ID)
    4: descontar turno perdido o habilitar lanzamiento
    """
    __tablename__ = "scheduled_events"

    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey("contracts.id", ondelete="CASCADE"), nullable=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id", ondelete="CASCADE"), nullable=False, index=True)
    target_account_id = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Target opportunity number of the team (e.g. if team has opportunity 2, due at 3, 4, 5)
    due_opportunity_number = Column(Integer, nullable=False, index=True)
    priority_step = Column(Integer, nullable=False)  # 1, 2, or 3
    installment_number = Column(Integer, default=1, nullable=False)
    
    event_type = Column(String(50), nullable=False)  # "liberar_ahorro", "bonificacion_diferida", "cuota_variable_e02", "cuota_fija_e14"
    status = Column(String(30), default="pendiente", nullable=False, index=True)  # "pendiente", "ejecutado", "vencido_pendiente", "cancelado", "revertido"
    
    amount_expected = Column(BigInteger, nullable=True)  # Fixed amount if known, or NULL if variable (E02)
    amount_executed = Column(BigInteger, default=0, nullable=False)
    
    metadata_json = Column(JSON, default=dict)
    executed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    contract = relationship("Contract", back_populates="scheduled_events")
    target_account = relationship("Account")
