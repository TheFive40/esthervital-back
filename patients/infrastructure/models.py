from sqlalchemy import Column, Integer, String, Date, DateTime, Numeric
from sqlalchemy.sql import func
from shared.database import Base

class Paciente(Base):
    __tablename__ = "pacientes"

    id_paciente = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    apellido = Column(String, nullable=False)
    fecha_nacimiento = Column(Date, nullable=False)
    edad = Column(Integer)
    peso_kg = Column(Numeric(5,2))

    telefono = Column(String)
    email = Column(String)
    direccion = Column(String)
    ocupacion = Column(String)

    numero_hijos = Column(Integer)
    tipo_parto = Column(String)

    tipo_identificacion = Column(String)
    numero_identificacion = Column(String, unique=True, nullable=False)

    estado = Column(String, default="Activo")
    fecha_registro = Column(DateTime(timezone=True), server_default=func.now())
