from sqlalchemy import Column, Integer, String, Date, Numeric, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from shared.database import Base

class Cita(Base):
    __tablename__ = "citas"

    id_cita = Column(Integer, primary_key=True, index=True)
    id_paciente = Column(Integer, ForeignKey("pacientes.id_paciente"), nullable=False)

    numero_cita = Column(Integer)  
    fecha = Column(Date, nullable=False)
    hora = Column(String, nullable=True) # HH:MM format
    procedimiento = Column(String, nullable=False)

    abdomen_alto_cm = Column(Numeric(5,2))
    cintura_cm = Column(Numeric(5,2))
    abdomen_bajo_cm = Column(Numeric(5,2))
    cadera_cm = Column(Numeric(5,2))

    firma = Column(String)

    estado = Column(String, default="Programada")
    fecha_registro = Column(DateTime(timezone=True), server_default=func.now())

    paciente = relationship("Paciente", backref="citas")
