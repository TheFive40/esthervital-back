from sqlalchemy import Column, Integer, String, Numeric, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, backref
from shared.database import Base


class CostoTratamiento(Base):
    """
    Almacena el costo total acordado para un tratamiento específico.
    Cada tratamiento tiene exactamente un registro de costo.
    """
    __tablename__ = "costos_tratamiento"

    id_costo = Column(Integer, primary_key=True, index=True)

    id_tratamiento = Column(
        Integer,
        ForeignKey("tratamientos.id_tratamiento", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    costo_total = Column(Numeric(12, 2), nullable=False)
    notas = Column(Text)
    fecha_registro = Column(DateTime(timezone=True), server_default=func.now())
    registrado_por = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=True)

    # Al eliminar Tratamiento → elimina CostoTratamiento (no nullifica)
    tratamiento = relationship(
        "Tratamiento",
        backref=backref("costo", uselist=False, cascade="all, delete-orphan"),
        uselist=False,
        passive_deletes=True,
    )
    usuario_registro = relationship("Usuario", foreign_keys=[registrado_por])

    @property
    def total_abonado(self) -> float:
        return float(
            sum(a.monto for a in self.abonos if a.estado == "Confirmado")
        )

    @property
    def saldo_pendiente(self) -> float:
        return float(self.costo_total) - self.total_abonado


class AbonoTratamiento(Base):
    """
    Registra cada pago parcial (abono) realizado por el paciente.
    """
    __tablename__ = "abonos_tratamiento"

    id_abono = Column(Integer, primary_key=True, index=True)

    id_costo = Column(
        Integer,
        ForeignKey("costos_tratamiento.id_costo", ondelete="CASCADE"),
        nullable=False,
    )

    monto = Column(Numeric(12, 2), nullable=False)
    medio_pago = Column(String(50))
    referencia = Column(String(100))
    estado = Column(String(20), default="Confirmado")
    fecha_pago = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    notas = Column(Text)
    fecha_registro = Column(DateTime(timezone=True), server_default=func.now())
    registrado_por = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=True)

    # Al eliminar CostoTratamiento → elimina AbonoTratamiento (no nullifica)
    costo = relationship(
        "CostoTratamiento",
        backref=backref("abonos", cascade="all, delete-orphan"),
        passive_deletes=True,
    )
    usuario_registro = relationship("Usuario", foreign_keys=[registrado_por])