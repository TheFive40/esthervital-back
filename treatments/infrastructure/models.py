from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from shared.database import Base


class Tratamiento(Base):
    __tablename__ = "tratamientos"

    id_tratamiento = Column(Integer, primary_key=True, index=True)
    id_paciente = Column(Integer, ForeignKey("pacientes.id_paciente"), nullable=False)
    id_usuario = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=False)

    nombre_tratamiento = Column(String(100), nullable=False)
    tipo_tratamiento = Column(String(20), nullable=False)
    descripcion = Column(Text)

    sesiones_planificadas = Column(Integer, nullable=False, default=1)

    estado = Column(String(20), default="Activo")
    fecha_inicio = Column(Date, nullable=False)
    fecha_fin = Column(Date)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())

    paciente = relationship("Paciente", backref="tratamientos")
    usuario = relationship("Usuario", backref="tratamientos")
    sesiones = relationship("SesionTratamiento", back_populates="tratamiento", cascade="all, delete-orphan")


class SesionTratamiento(Base):
    __tablename__ = "sesiones_tratamiento"

    id_sesion = Column(Integer, primary_key=True, index=True)
    id_tratamiento = Column(Integer, ForeignKey("tratamientos.id_tratamiento"), nullable=False)

    numero_sesion = Column(Integer, nullable=False)
    fecha_sesion = Column(DateTime, nullable=False)

    notas = Column(Text)
    estado = Column(String(20), default="Completada")

    abdomen_alto_cm = Column(Integer)
    cintura_cm = Column(Integer)
    abdomen_bajo_cm = Column(Integer)
    cadera_cm = Column(Integer)
    peso_kg = Column(Integer)
    zonas_trabajadas = Column(Text)  # JSON array of body zones

    fecha_registro = Column(DateTime(timezone=True), server_default=func.now())

    tratamiento = relationship("Tratamiento", back_populates="sesiones")
    imagenes = relationship("ImagenSesion", back_populates="sesion", cascade="all, delete-orphan")


class ImagenSesion(Base):
    __tablename__ = "imagenes_sesion"

    id_imagen = Column(Integer, primary_key=True, index=True)
    id_sesion = Column(Integer, ForeignKey("sesiones_tratamiento.id_sesion"), nullable=False)

    url_imagen = Column(String(500), nullable=False)
    descripcion = Column(String(200))
    tipo_imagen = Column(String(50))

    fecha_subida = Column(DateTime(timezone=True), server_default=func.now())

    sesion = relationship("SesionTratamiento", back_populates="imagenes")