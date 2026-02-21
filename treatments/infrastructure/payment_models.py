from sqlalchemy import Column, Integer, String, Numeric, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from shared.database import Base


class CostoTratamiento(Base):
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

    tratamiento = relationship("Tratamiento", backref="costo", uselist=False)
    usuario_registro = relationship("Usuario", foreign_keys=[registrado_por])

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
        return float(self.costo_total) - self.total_abonado


class AbonoTratamiento(Base):

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

    fecha_pago = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    notas = Column(Text)

    fecha_registro = Column(DateTime(timezone=True), server_default=func.now())
    registrado_por = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=True)

    costo = relationship("CostoTratamiento", backref="abonos")
    usuario_registro = relationship("Usuario", foreign_keys=[registrado_por])