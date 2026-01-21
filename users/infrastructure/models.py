from sqlalchemy import (
    Integer, String, Text, ForeignKey, DateTime
)
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from shared.database import Base


class Rol(Base):
    __tablename__ = "roles"

    id_rol: Mapped[int] = mapped_column(primary_key=True)
    nombre_rol: Mapped[str] = mapped_column(String(50), nullable=False)
    descripcion: Mapped[str] = mapped_column(Text)

    permisos = relationship("RolPermiso", back_populates="rol")


class Permiso(Base):
    __tablename__ = "permisos"

    id_permiso: Mapped[int] = mapped_column(primary_key=True)
    nombre_permiso: Mapped[str] = mapped_column(String(100), nullable=False)
    modulo: Mapped[str] = mapped_column(String(100))
    descripcion: Mapped[str] = mapped_column(Text)


class RolPermiso(Base):
    __tablename__ = "roles_permisos"

    id_rol_permiso: Mapped[int] = mapped_column(primary_key=True)
    id_rol: Mapped[int] = mapped_column(ForeignKey("roles.id_rol"))
    id_permiso: Mapped[int] = mapped_column(ForeignKey("permisos.id_permiso"))

    rol = relationship("Rol", back_populates="permisos")
    permiso = relationship("Permiso")


class Usuario(Base):
    __tablename__ = "usuarios"

    id_usuario: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100))
    apellido: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)

    estado: Mapped[str] = mapped_column(String(20))
    fecha_creacion: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now()
    )

    id_rol: Mapped[int] = mapped_column(ForeignKey("roles.id_rol"))
    rol = relationship("Rol")
