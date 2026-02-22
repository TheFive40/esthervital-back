from sqlalchemy import Column, Integer, String, Numeric, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from shared.database import Base


class CostoTratamiento(Base):
    """
    Almacena el costo total acordado para un tratamiento específico.
    Cada tratamiento tiene exactamente un registro de costo.
    """
    __tablename__ = "costos_tratamiento"

    id_costo = Column(Integer, primary_key=True, index=True)

    # Relación 1-a-1 con el tratamiento
    id_tratamiento = Column(
        Integer,
        ForeignKey("tratamientos.id_tratamiento", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    # Costo total pactado con el paciente (en pesos colombianos)
    costo_total = Column(Numeric(12, 2), nullable=False)

    # Notas sobre la tarifa (ej: "precio de temporada", "descuento aplicado", etc.)
    notas = Column(Text)

    fecha_registro = Column(DateTime(timezone=True), server_default=func.now())
    registrado_por = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=True)

    # Relaciones
    tratamiento = relationship("Tratamiento", backref="costo", uselist=False)
    usuario_registro = relationship("Usuario", foreign_keys=[registrado_por])

    # Computed helpers (acceso rápido en Python)
    @property
    def total_abonado(self) -> float:
        """Suma de todos los abonos confirmados."""
        return float(
            sum(
                a.monto
                for a in self.abonos
                if a.estado == "Confirmado"
            )
        )

    @property
    def saldo_pendiente(self) -> float:
        """Saldo que aún debe el paciente."""
        return float(self.costo_total) - self.total_abonado


class AbonoTratamiento(Base):
    """
    Registra cada pago parcial (abono) realizado por el paciente
    hacia el costo total de un tratamiento.
    """
    __tablename__ = "abonos_tratamiento"

    id_abono = Column(Integer, primary_key=True, index=True)

    id_costo = Column(
        Integer,
        ForeignKey("costos_tratamiento.id_costo", ondelete="CASCADE"),
        nullable=False,
    )

    monto = Column(Numeric(12, 2), nullable=False)

    medio_pago = Column(String(50))  # "Efectivo", "Transferencia", "Tarjeta débito", etc.

    referencia = Column(String(100))

    estado = Column(String(20), default="Confirmado")  # "Confirmado", "Anulado"

    # Fecha en que se realizó el pago (puede diferir de fecha_registro)
    fecha_pago = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    notas = Column(Text)

    fecha_registro = Column(DateTime(timezone=True), server_default=func.now())
    registrado_por = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=True)

    # Relaciones
    costo = relationship("CostoTratamiento", backref="abonos")
    usuario_registro = relationship("Usuario", foreign_keys=[registrado_por])