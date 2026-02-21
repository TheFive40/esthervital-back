from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from shared.database import Base


class ConsentimientoPaciente(Base):

    __tablename__ = "consentimientos_paciente"

    id_consentimiento = Column(Integer, primary_key=True, index=True)
    id_paciente = Column(Integer, ForeignKey("pacientes.id_paciente"), nullable=False)

    tipo_consentimiento = Column(String(100), nullable=False)

    url_archivo = Column(String(500), nullable=False)

    nombre_archivo = Column(String(255), nullable=False)

    tipo_archivo = Column(String(50))

    observaciones = Column(Text)

    activo = Column(Boolean, default=True, nullable=False)

    fecha_subida = Column(DateTime(timezone=True), server_default=func.now())
    subido_por = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=True)

    paciente = relationship("Paciente", backref="consentimientos")
    usuario_subida = relationship("Usuario", foreign_keys=[subido_por])