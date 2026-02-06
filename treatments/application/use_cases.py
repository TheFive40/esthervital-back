from sqlalchemy.orm import Session
from treatments.infrastructure.models import Tratamiento, SesionTratamiento, ImagenSesion
from treatments.infrastructure.repository import (
    TratamientoRepository,
    SesionRepository,
    ImagenRepository
)
from treatments.presentation.schemas import (
    TratamientoCreate, TratamientoUpdate, TratamientoResponse, TratamientoDetallado,
    SesionCreate, SesionUpdate,
    ImagenCreate, ImagenUpdate
)
from typing import Optional

tratamiento_repo = TratamientoRepository()
sesion_repo = SesionRepository()
imagen_repo = ImagenRepository()


def crear_tratamiento(db: Session, data: TratamientoCreate):
    tratamiento = Tratamiento(**data.dict())
    return tratamiento_repo.create(db, tratamiento)


def listar_tratamientos(db: Session):
    """Returns all treatments - use listar_tratamientos_paginados for large datasets"""
    tratamientos = tratamiento_repo.get_all(db)
    resultado = []

    for trat in tratamientos:
        sesiones_completadas = sesion_repo.count_by_tratamiento(db, trat.id_tratamiento)

        resultado.append({
            **trat.__dict__,
            "sesiones_completadas": sesiones_completadas,
            "paciente_nombre": f"{trat.paciente.nombre} {trat.paciente.apellido}" if trat.paciente else None,
            "usuario_nombre": f"{trat.usuario.nombre} {trat.usuario.apellido}" if trat.usuario else None
        })

    return resultado


def listar_tratamientos_paginados(
    db: Session,
    skip: int = 0,
    limit: int = 50,
    estado: Optional[str] = None,
    id_paciente: Optional[int] = None,
    search: Optional[str] = None
) -> tuple[list, int]:
    """
    Get paginated treatments with filtering.
    Returns: (list of treatments with computed fields, total count)
    """
    tratamientos, total = tratamiento_repo.get_paginated(
        db, skip, limit, estado, id_paciente, search
    )
    
    resultado = []
    for trat in tratamientos:
        sesiones_completadas = sesion_repo.count_by_tratamiento(db, trat.id_tratamiento)

        resultado.append({
            **trat.__dict__,
            "sesiones_completadas": sesiones_completadas,
            "paciente_nombre": f"{trat.paciente.nombre} {trat.paciente.apellido}" if trat.paciente else None,
            "usuario_nombre": f"{trat.usuario.nombre} {trat.usuario.apellido}" if trat.usuario else None
        })

    return resultado, total


def obtener_tratamiento(db: Session, id_tratamiento: int):
    return tratamiento_repo.get_by_id(db, id_tratamiento)


def obtener_tratamiento_detallado(db: Session, id_tratamiento: int):
    tratamiento = tratamiento_repo.get_by_id(db, id_tratamiento)
    if not tratamiento:
        return None

    sesiones_completadas = sesion_repo.count_by_tratamiento(db, id_tratamiento)

    return {
        **tratamiento.__dict__,
        "sesiones_completadas": sesiones_completadas,
        "paciente_nombre": f"{tratamiento.paciente.nombre} {tratamiento.paciente.apellido}",
        "usuario_nombre": f"{tratamiento.usuario.nombre} {tratamiento.usuario.apellido}",
        "sesiones": tratamiento.sesiones
    }


def obtener_tratamientos_por_paciente(db: Session, id_paciente: int):
    tratamientos = tratamiento_repo.get_by_paciente(db, id_paciente)
    resultado = []

    for trat in tratamientos:
        sesiones_completadas = sesion_repo.count_by_tratamiento(db, trat.id_tratamiento)

        resultado.append({
            **trat.__dict__,
            "sesiones_completadas": sesiones_completadas,
            "usuario_nombre": f"{trat.usuario.nombre} {trat.usuario.apellido}" if trat.usuario else None
        })

    return resultado


def actualizar_tratamiento(db: Session, id_tratamiento: int, data: TratamientoUpdate):
    tratamiento = tratamiento_repo.get_by_id(db, id_tratamiento)
    if not tratamiento:
        return None

    for key, value in data.dict(exclude_unset=True).items():
        setattr(tratamiento, key, value)

    return tratamiento_repo.update(db, tratamiento)


def eliminar_tratamiento(db: Session, id_tratamiento: int):
    tratamiento = tratamiento_repo.get_by_id(db, id_tratamiento)
    if not tratamiento:
        return None
    tratamiento_repo.delete(db, tratamiento)
    return True


def crear_sesion(db: Session, data: SesionCreate):
    sesion = SesionTratamiento(**data.dict())
    return sesion_repo.create(db, sesion)


def listar_sesiones_tratamiento(db: Session, id_tratamiento: int):
    return sesion_repo.get_by_tratamiento(db, id_tratamiento)


def obtener_sesion(db: Session, id_sesion: int):
    return sesion_repo.get_by_id(db, id_sesion)


def actualizar_sesion(db: Session, id_sesion: int, data: SesionUpdate):
    sesion = sesion_repo.get_by_id(db, id_sesion)
    if not sesion:
        return None

    for key, value in data.dict(exclude_unset=True).items():
        setattr(sesion, key, value)

    return sesion_repo.update(db, sesion)


def eliminar_sesion(db: Session, id_sesion: int):
    sesion = sesion_repo.get_by_id(db, id_sesion)
    if not sesion:
        return None
    sesion_repo.delete(db, sesion)
    return True


def crear_imagen(db: Session, data: ImagenCreate):
    imagen = ImagenSesion(**data.dict())
    return imagen_repo.create(db, imagen)


def listar_imagenes_sesion(db: Session, id_sesion: int):
    return imagen_repo.get_by_sesion(db, id_sesion)


def obtener_imagen(db: Session, id_imagen: int):
    return imagen_repo.get_by_id(db, id_imagen)


def actualizar_imagen(db: Session, id_imagen: int, data: ImagenUpdate):
    imagen = imagen_repo.get_by_id(db, id_imagen)
    if not imagen:
        return None

    for key, value in data.dict(exclude_unset=True).items():
        setattr(imagen, key, value)

    return imagen_repo.update(db, imagen)


def eliminar_imagen(db: Session, id_imagen: int):
    imagen = imagen_repo.get_by_id(db, id_imagen)
    if not imagen:
        return None
    imagen_repo.delete(db, imagen)
    return True