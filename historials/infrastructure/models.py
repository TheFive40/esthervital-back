from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from shared.database import Base

class HistorialClinico(Base):
    __tablename__ = "historiales_clinicos"

    id_historial = Column(Integer, primary_key=True, index=True)
    id_paciente = Column(Integer, ForeignKey("pacientes.id_paciente"), nullable=False)

    motivo_consulta = Column(Text)
    diagnostico = Column(Text)
    tratamiento = Column(Text)

    sesiones_planificadas = Column(Integer)
    fecha_ingreso = Column(DateTime(timezone=True), server_default=func.now())

    paciente = relationship("Paciente", backref="historiales")
    documentos = relationship("DocumentoClinico", backref="historial", cascade="all, delete-orphan")

class DocumentoClinico(Base):
    __tablename__ = "documentos_clinicos"

    id_documento = Column(Integer, primary_key=True, index=True)
    id_historial = Column(Integer, ForeignKey("historiales_clinicos.id_historial"), nullable=False)

    tipo_documento = Column(String) 
    url_archivo = Column(String)
    descripcion = Column(Text)
    fecha_subida = Column(DateTime(timezone=True), server_default=func.now())
