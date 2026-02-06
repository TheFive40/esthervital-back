"""
Router protegido para Citas/Appointments
Incluye autenticación, autorización, rate limiting y auditoría
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date
import math

from shared.database import get_db
from shared.dependencies import (
    get_current_user,
    get_current_employee,
    require_permission,
    require_write_rate_limit
)
from shared.security_utils import AuditLogger

from appointments.application.use_cases import CitaService
from appointments.presentation.schemas import CitaCreate, CitaUpdate, CitaRead, PaginatedCitasResponse

router = APIRouter(prefix="/citas", tags=["Citas"])


# ============ CITAS ENDPOINTS ============

@router.post(
    "/",
    response_model=CitaRead,
    dependencies=[
        Depends(require_permission("create_appointment")),
        Depends(require_write_rate_limit())
    ]
)
async def crear_cita(
        cita: CitaCreate,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user),
        request: Request = None
):
    """
    Crear nueva cita

    Requiere:
    - Autenticación
    - Permiso: create_appointment
    - Rate limit: 50 writes/minuto

    Roles permitidos:
    - Administrador
    - Empleado

    Campos:
    - id_paciente: ID del paciente
    - numero_cita: Número secuencial de la cita
    - fecha: Fecha de la cita (YYYY-MM-DD)
    - hora: Hora de la cita (HH:MM)
    - procedimiento: Tipo de procedimiento
    - medidas: Abdominal alto, cintura, abdominal bajo, cadera (opcional)
    """
    client_ip = request.client.host if request.client else current_user.get("ip_address")

    try:
        service = CitaService(db)
        nuevo = service.crear_cita(cita.dict())

        # Log successful creation
        AuditLogger.log_action(
            user_id=current_user["user_id"],
            action="create_cita",
            resource="cita",
            resource_id=nuevo.id_cita,
            status="success",
            details={
                "id_paciente": cita.id_paciente,
                "procedimiento": cita.procedimiento,
                "fecha": str(cita.fecha)
            },
            ip_address=client_ip
        )

        return nuevo

    except Exception as e:
        AuditLogger.log_action(
            user_id=current_user["user_id"],
            action="create_cita",
            resource="cita",
            status="failed",
            details={"error": str(e)},
            ip_address=client_ip
        )
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/",
    response_model=PaginatedCitasResponse,
    dependencies=[Depends(require_permission("read_appointment"))]
)
async def listar_citas(
        page: int = 1,
        limit: int = 50,
        estado: Optional[str] = None,
        fecha: Optional[str] = None,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user),
        request: Request = None
):
    """
    Listar todas las citas (con paginación optimizada a nivel SQL)

    Requiere:
    - Autenticación
    - Permiso: read_appointment

    Query params:
    - page: Número de página (default: 1)
    - limit: Máximo de registros a retornar (default: 50, max: 100)
    - estado: Filtrar por estado (Pendiente/Completada/Cancelada)
    - fecha: Filtrar por fecha (YYYY-MM-DD)
    """
    # Límite máximo de registros
    limit = min(limit, 100)
    skip = (page - 1) * limit

    client_ip = request.client.host if request.client else current_user.get("ip_address")

    try:
        service = CitaService(db)
        
        # Parse date if provided
        fecha_parsed = None
        if fecha:
            try:
                fecha_parsed = date.fromisoformat(fecha)
            except ValueError:
                pass
        
        # Use optimized paginated query (SQL level pagination)
        citas, total = service.listar_citas_paginadas(
            skip=skip,
            limit=limit,
            estado=estado,
            fecha=fecha_parsed
        )
        
        total_pages = math.ceil(total / limit) if limit > 0 else 0

        # Log access
        AuditLogger.log_action(
            user_id=current_user["user_id"],
            action="list_citas",
            resource="cita",
            status="success",
            details={
                "count": len(citas),
                "page": page,
                "limit": limit,
                "total": total,
                "estado_filter": estado,
                "fecha_filter": fecha
            },
            ip_address=client_ip
        )

        return PaginatedCitasResponse(
            data=citas,
            total=total,
            page=page,
            limit=limit,
            total_pages=total_pages
        )

    except Exception as e:
        AuditLogger.log_action(
            user_id=current_user["user_id"],
            action="list_citas",
            resource="cita",
            status="failed",
            details={"error": str(e)},
            ip_address=client_ip
        )
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/paciente/{id_paciente}",
    response_model=List[CitaRead],
    dependencies=[Depends(require_permission("read_appointment"))]
)
async def listar_citas_paciente(
        id_paciente: int,
        skip: int = 0,
        limit: int = 50,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user),
        request: Request = None
):
    """
    Listar citas de un paciente específico

    Requiere:
    - Autenticación
    - Permiso: read_appointment

    Parámetros:
    - id_paciente: ID del paciente
    - skip: Número de registros a saltar (default: 0)
    - limit: Máximo de registros a retornar (default: 50, max: 100)
    """
    # Límite máximo de registros
    limit = min(limit, 100)

    client_ip = request.client.host if request.client else current_user.get("ip_address")

    try:
        service = CitaService(db)
        citas = service.listar_citas_paciente(id_paciente)

        # Apply pagination
        citas = citas[skip:skip + limit]

        # Log access
        AuditLogger.log_action(
            user_id=current_user["user_id"],
            action="list_citas_paciente",
            resource="cita",
            resource_id=id_paciente,
            status="success",
            details={"count": len(citas), "skip": skip, "limit": limit},
            ip_address=client_ip
        )

        return citas

    except Exception as e:
        AuditLogger.log_action(
            user_id=current_user["user_id"],
            action="list_citas_paciente",
            resource="cita",
            status="failed",
            details={"error": str(e)},
            ip_address=client_ip
        )
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/{id_cita}",
    response_model=CitaRead,
    dependencies=[Depends(require_permission("read_appointment"))]
)
async def obtener_cita(
        id_cita: int,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user),
        request: Request = None
):
    """
    Obtener detalles de una cita específica

    Requiere:
    - Autenticación
    - Permiso: read_appointment
    """
    client_ip = request.client.host if request.client else current_user.get("ip_address")

    service = CitaService(db)
    cita = service.obtener_cita(id_cita)

    if not cita:
        AuditLogger.log_action(
            user_id=current_user["user_id"],
            action="read_cita",
            resource="cita",
            resource_id=id_cita,
            status="failed",
            details={"reason": "not_found"},
            ip_address=client_ip
        )
        raise HTTPException(status_code=404, detail="Cita no encontrada")

    # Log successful access
    AuditLogger.log_action(
        user_id=current_user["user_id"],
        action="read_cita",
        resource="cita",
        resource_id=id_cita,
        status="success",
        ip_address=client_ip
    )

    return cita


@router.put(
    "/{id_cita}",
    response_model=CitaRead,
    dependencies=[
        Depends(require_permission("update_appointment")),
        Depends(require_write_rate_limit())
    ]
)
async def actualizar_cita(
        id_cita: int,
        data: CitaUpdate,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user),
        request: Request = None
):
    """
    Actualizar información de cita

    Requiere:
    - Autenticación
    - Permiso: update_appointment
    - Rate limit: 50 writes/minuto

    Permite actualizar:
    - Fecha y hora
    - Procedimiento
    - Medidas corporales
    - Estado (Programada/Realizada/Cancelada)
    - Firma del paciente
    """
    client_ip = request.client.host if request.client else current_user.get("ip_address")

    service = CitaService(db)
    cita_actualizada = service.actualizar_cita(
        id_cita,
        data.dict(exclude_unset=True)
    )

    if not cita_actualizada:
        AuditLogger.log_action(
            user_id=current_user["user_id"],
            action="update_cita",
            resource="cita",
            resource_id=id_cita,
            status="failed",
            details={"reason": "not_found"},
            ip_address=client_ip
        )
        raise HTTPException(status_code=404, detail="Cita no encontrada")

    # Log successful update
    AuditLogger.log_action(
        user_id=current_user["user_id"],
        action="update_cita",
        resource="cita",
        resource_id=id_cita,
        status="success",
        details={
            "procedimiento": data.procedimiento,
            "estado": data.estado,
            "fecha": str(data.fecha) if data.fecha else None
        },
        ip_address=client_ip
    )

    return cita_actualizada


@router.delete(
    "/{id_cita}",
    response_model=dict,
    dependencies=[
        Depends(require_permission("delete_appointment")),
        Depends(require_write_rate_limit())
    ]
)
async def eliminar_cita(
        id_cita: int,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user),
        request: Request = None
):
    """
    Eliminar cita

    Requiere:
    - Autenticación
    - Permiso: delete_appointment
    - Rate limit: 50 writes/minuto

    Nota: Eliminación lógica (soft delete)
    """
    client_ip = request.client.host if request.client else current_user.get("ip_address")

    service = CitaService(db)
    eliminado = service.eliminar_cita(id_cita)

    if not eliminado:
        AuditLogger.log_action(
            user_id=current_user["user_id"],
            action="delete_cita",
            resource="cita",
            resource_id=id_cita,
            status="failed",
            details={"reason": "not_found"},
            ip_address=client_ip
        )
        raise HTTPException(status_code=404, detail="Cita no encontrada")

    # Log successful deletion
    AuditLogger.log_action(
        user_id=current_user["user_id"],
        action="delete_cita",
        resource="cita",
        resource_id=id_cita,
        status="success",
        ip_address=client_ip
    )

    return {"message": "Cita eliminada correctamente"}


# ============ ENDPOINTS ADICIONALES ============

@router.get(
    "/estadisticas/dia",
    response_model=dict,
    dependencies=[Depends(require_permission("read_appointment"))]
)
async def obtener_estadisticas_citas_hoy(
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user),
        request: Request = None
):
    """
    Obtener estadísticas de citas de hoy

    Requiere:
    - Autenticación
    - Permiso: read_appointment

    Retorna:
    - Total de citas programadas
    - Citas realizadas
    - Citas canceladas
    - Próximas citas en las próximas 2 horas
    """
    client_ip = request.client.host if request.client else current_user.get("ip_address")

    try:
        from datetime import date

        service = CitaService(db)
        todas_citas = service.listar_citas()

        # Filtrar citas de hoy
        hoy = date.today()
        citas_hoy = [c for c in todas_citas if c.fecha == hoy]

        # Estadísticas
        stats = {
            "fecha": str(hoy),
            "total_citas": len(citas_hoy),
            "programadas": len([c for c in citas_hoy if c.estado == "Programada"]),
            "realizadas": len([c for c in citas_hoy if c.estado == "Realizada"]),
            "canceladas": len([c for c in citas_hoy if c.estado == "Cancelada"]),
            "citas": [
                {
                    "id": c.id_cita,
                    "paciente_id": c.id_paciente,
                    "hora": c.hora,
                    "procedimiento": c.procedimiento,
                    "estado": c.estado
                }
                for c in citas_hoy
            ]
        }

        # Log access
        AuditLogger.log_action(
            user_id=current_user["user_id"],
            action="view_estadisticas_citas",
            resource="cita",
            status="success",
            ip_address=client_ip
        )

        return stats

    except Exception as e:
        AuditLogger.log_action(
            user_id=current_user["user_id"],
            action="view_estadisticas_citas",
            resource="cita",
            status="failed",
            details={"error": str(e)},
            ip_address=client_ip
        )
        raise HTTPException(status_code=400, detail=str(e))


@router.put(
    "/{id_cita}/marcar-realizada",
    response_model=CitaRead,
    dependencies=[
        Depends(require_permission("update_appointment")),
        Depends(require_write_rate_limit())
    ]
)
async def marcar_cita_realizada(
        id_cita: int,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user),
        request: Request = None
):
    """
    Marcar cita como realizada

    Requiere:
    - Autenticación
    - Permiso: update_appointment

    Endpoint conveniente para cambiar estado a "Realizada"
    """
    client_ip = request.client.host if request.client else current_user.get("ip_address")

    service = CitaService(db)
    cita_actualizada = service.actualizar_cita(
        id_cita,
        {"estado": "Realizada"}
    )

    if not cita_actualizada:
        AuditLogger.log_action(
            user_id=current_user["user_id"],
            action="mark_cita_realizada",
            resource="cita",
            resource_id=id_cita,
            status="failed",
            details={"reason": "not_found"},
            ip_address=client_ip
        )
        raise HTTPException(status_code=404, detail="Cita no encontrada")

    # Log successful update
    AuditLogger.log_action(
        user_id=current_user["user_id"],
        action="mark_cita_realizada",
        resource="cita",
        resource_id=id_cita,
        status="success",
        ip_address=client_ip
    )

    return cita_actualizada


@router.put(
    "/{id_cita}/cancelar",
    response_model=CitaRead,
    dependencies=[
        Depends(require_permission("update_appointment")),
        Depends(require_write_rate_limit())
    ]
)
async def cancelar_cita(
        id_cita: int,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user),
        request: Request = None
):
    """
    Cancelar cita

    Requiere:
    - Autenticación
    - Permiso: update_appointment

    Endpoint conveniente para cambiar estado a "Cancelada"
    """
    client_ip = request.client.host if request.client else current_user.get("ip_address")

    service = CitaService(db)
    cita_actualizada = service.actualizar_cita(
        id_cita,
        {"estado": "Cancelada"}
    )

    if not cita_actualizada:
        AuditLogger.log_action(
            user_id=current_user["user_id"],
            action="cancel_cita",
            resource="cita",
            resource_id=id_cita,
            status="failed",
            details={"reason": "not_found"},
            ip_address=client_ip
        )
        raise HTTPException(status_code=404, detail="Cita no encontrada")

    # Log successful cancellation
    AuditLogger.log_action(
        user_id=current_user["user_id"],
        action="cancel_cita",
        resource="cita",
        resource_id=id_cita,
        status="success",
        ip_address=client_ip
    )

    return cita_actualizada