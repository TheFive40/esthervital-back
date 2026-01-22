from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey
from shared.database import Base

class Tratamiento(Base):
    __tablename__ = "tratamientos"

    id_tratamiento = Column(Integer, primary_key=True, index=True)
    id_paciente = Column(Integer, ForeignKey("pacientes.id_paciente"), nullable=False)

    nombre_tratamiento = Column(String(100), nullable=False)
    tipo_tratamiento = Column(String(20), nullable=False)  # Facial | Corporal
    descripcion = Column(Text)

    estado = Column(String(20), default="Activo")  # Activo | Finalizado | Suspendido
    fecha_inicio = Column(Date, nullable=False)
    fecha_fin = Column(Date)
