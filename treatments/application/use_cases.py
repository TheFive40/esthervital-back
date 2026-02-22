from sqlalchemy.orm import Session
from treatments.infrastructure.models import Tratamiento, SesionTratamiento, ImagenSesion
from treatments.infrastructure.repository import (
    TratamientoRepository,
    SesionRepository,
    ImagenRepository,
)
from treatments.presentation.schemas import (
    TratamientoCreate, TratamientoUpdate,
    SesionCreate, SesionUpdate,
    ImagenCreate, ImagenUpdate,
)
from typing import Optional

tratamiento_repo = TratamientoRepository()
sesion_repo = SesionRepository()
imagen_repo = ImagenRepository()


def _build_financiero(trat: Tratamiento) -> Optional[dict]:
    costo_raw = getattr(trat, "costo", None)

    # Manejar tanto uselist=False (objeto) como uselist=True (lista)
    if isinstance(costo_raw, list):
        costo = costo_raw[0] if costo_raw else None
    else:
        costo = costo_raw

    if not costo:
        return None

    total = float(costo.costo_total)
    abonado = costo.total_abonado
    saldo = costo.saldo_pendiente
    if abonado == 0:
        estado_pago = "Pendiente"
    elif saldo <= 0:
        estado_pago = "Pagado"
    else:
        estado_pago = "Abono parcial"

    return {
        "id_costo": costo.id_costo,
        "costo_total": total,
        "total_abonado": abonado,
        "saldo_pendiente": max(saldo, 0),
        "estado_pago": estado_pago,
        "cantidad_abonos": len([a for a in costo.abonos if a.estado == "Confirmado"]),
    }


def crear_tratamiento(db: Session, data: TratamientoCreate, registrado_por: Optional[int] = None):
    """
    Crea el tratamiento y, si se envía costo_total, registra el CostoTratamiento
    en la misma transacción (atómico: si falla uno, se revierte todo).
    """
    from decimal import Decimal
    from treatments.infrastructure.payment_models import CostoTratamiento

    # 1. Construir tratamiento (sin costo_total, que no es columna del modelo)
    trat_data = data.dict(exclude={"costo_total", "notas_costo"})
    tratamiento = Tratamiento(**trat_data)
    db.add(tratamiento)
    db.flush()  # Obtener id_tratamiento sin hacer commit todavía

    # 2. Si viene costo_total, crear el registro de costo en la misma transacción
    if data.costo_total is not None:
        costo = CostoTratamiento(
            id_tratamiento=tratamiento.id_tratamiento,
            costo_total=data.costo_total,
            notas=data.notas_costo,
            registrado_por=registrado_por,
        )
        db.add(costo)

    # 3. Commit único → atómico
    db.commit()
    db.refresh(tratamiento)

    # 4. Recargar con relaciones para construir respuesta
    return _enriquecer_tratamiento(db, tratamiento)


def _enriquecer_tratamiento(db: Session, trat: Tratamiento) -> dict:
    """Construye el dict de respuesta con campos calculados."""
    sesiones_completadas = sesion_repo.count_by_tratamiento(db, trat.id_tratamiento)
    return {
        **trat.__dict__,
        "sesiones_completadas": sesiones_completadas,
        "paciente_nombre": (
            f"{trat.paciente.nombre} {trat.paciente.apellido}" if trat.paciente else None
        ),
        "usuario_nombre": (
            f"{trat.usuario.nombre} {trat.usuario.apellido}" if trat.usuario else None
        ),
        "financiero": _build_financiero(trat),
    }


def listar_tratamientos(db: Session):
    """Returns all treatments - use listar_tratamientos_paginados for large datasets"""
    tratamientos = tratamiento_repo.get_all(db)

    # Batch count completed sessions (fixes N+1)
    trat_ids = [t.id_tratamiento for t in tratamientos]
    count_map = sesion_repo.count_by_tratamientos_batch(db, trat_ids)

    resultado = []
    for trat in tratamientos:
        resultado.append({
            **trat.__dict__,
            "sesiones_completadas": count_map.get(trat.id_tratamiento, 0),
            "paciente_nombre": f"{trat.paciente.nombre} {trat.paciente.apellido}" if trat.paciente else None,
            "usuario_nombre": f"{trat.usuario.nombre} {trat.usuario.apellido}" if trat.usuario else None,
            "financiero": _build_financiero(trat),
        })

    return resultado


def listar_tratamientos_paginados(
    db: Session,
    skip: int = 0,
    limit: int = 50,
    estado: Optional[str] = None,
    id_paciente: Optional[int] = None,
    search: Optional[str] = None,
) -> tuple[list, int]:
    tratamientos, total = tratamiento_repo.get_paginated(
        db, skip, limit, estado, id_paciente, search
    )

    trat_ids = [t.id_tratamiento for t in tratamientos]
    count_map = sesion_repo.count_by_tratamientos_batch(db, trat_ids)

    resultado = []
    for trat in tratamientos:
        resultado.append({
            **trat.__dict__,
            "sesiones_completadas": count_map.get(trat.id_tratamiento, 0),
            "paciente_nombre": f"{trat.paciente.nombre} {trat.paciente.apellido}" if trat.paciente else None,
            "usuario_nombre": f"{trat.usuario.nombre} {trat.usuario.apellido}" if trat.usuario else None,
            "financiero": _build_financiero(trat),
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
        "sesiones": tratamiento.sesiones,
        "financiero": _build_financiero(tratamiento),
    }


def obtener_tratamientos_por_paciente(db: Session, id_paciente: int):
    tratamientos = tratamiento_repo.get_by_paciente(db, id_paciente)
    resultado = []

    for trat in tratamientos:
        sesiones_completadas = sesion_repo.count_by_tratamiento(db, trat.id_tratamiento)
        resultado.append({
            **trat.__dict__,
            "sesiones_completadas": sesiones_completadas,
            "usuario_nombre": f"{trat.usuario.nombre} {trat.usuario.apellido}" if trat.usuario else None,
            "financiero": _build_financiero(trat),
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


# ── Sesiones ──────────────────────────────────────────────────────────────────

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


# ── Imágenes ──────────────────────────────────────────────────────────────────

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