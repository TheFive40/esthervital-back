"""
Ejemplo de router protegido: Pacientes
Este archivo muestra cómo actualizar los routers existentes
para incluir autenticación, autorización y rate limiting
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List, Optional

from shared.database import get_db
from shared.dependencies import (
    get_current_user,
    get_current_employee,
    require_permission,
    require_write_rate_limit,
    verify_patient_access
)
from shared.security_utils import AuditLogger

from patients.application.use_cases import PacienteService
from patients.presentation.schemas import PacienteCreate, PacienteUpdate, PacienteRead

router = APIRouter(prefix="/pacientes", tags=["Pacientes"])


@router.post(
    "/",
    response_model=PacienteRead,
    dependencies=[
        Depends(require_permission("create_patient")),
        Depends(require_write_rate_limit())
    ]
)
async def crear_paciente(
        paciente: PacienteCreate,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user),
        request: Request = None
):
    """
    Crear nuevo paciente

    Requiere:
    - Autenticación (JWT token)
    - Permiso: create_patient
    - Rate limit: 50 writes/minuto

    Roles permitidos:
    - Administrador
    - Empleado
    """
    client_ip = request.client.host if request.client else current_user.get("ip_address")

    try:
        service = PacienteService(db)
        nuevo_paciente = service.crear_paciente(paciente.dict())

        # Log successful creation
        AuditLogger.log_action(
            user_id=current_user["user_id"],
            action="create_patient",
            resource="paciente",
            resource_id=nuevo_paciente.id_paciente,
            status="success",
            details={
                "nombre": paciente.nombre,
                "identificacion": paciente.numero_identificacion
            },
            ip_address=client_ip
        )

        return nuevo_paciente

    except Exception as e:
        AuditLogger.log_action(
            user_id=current_user["user_id"],
            action="create_patient",
            resource="paciente",
            status="failed",
            details={"error": str(e)},
            ip_address=client_ip
        )
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/",
    response_model=List[PacienteRead],
    dependencies=[Depends(require_permission("read_patient"))]
)
async def listar_pacientes(
        skip: int = 0,
        limit: int = 50,
        estado: Optional[str] = None,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user),
        request: Request = None
):
    """
    Listar todos los pacientes (con paginación)

    Requiere:
    - Autenticación
    - Permiso: read_patient

    Query params:
    - skip: Número de registros a saltar (default: 0)
    - limit: Máximo de registros a retornar (default: 50, max: 100)
    - estado: Filtrar por estado (Activo/Inactivo)
    """
    # Límite máximo de registros
    limit = min(limit, 100)

    client_ip = request.client.host if request.client else current_user.get("ip_address")

    service = PacienteService(db)
    pacientes = service.listar_pacientes()

    # Filter by status if provided
    if estado:
        pacientes = [p for p in pacientes if p.estado == estado]

    # Apply pagination
    pacientes = pacientes[skip:skip + limit]

    # Log access
    AuditLogger.log_action(
        user_id=current_user["user_id"],
        action="list_patients",
        resource="paciente",
        status="success",
        details={"count": len(pacientes), "skip": skip, "limit": limit},
        ip_address=client_ip
    )

    return pacientes


@router.get(
    "/{id_paciente}",
    response_model=PacienteRead,
    dependencies=[Depends(require_permission("read_patient"))]
)
async def obtener_paciente(
        id_paciente: int,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user),
        request: Request = None
):
    """
    Obtener detalles de un paciente específico

    Requiere:
    - Autenticación
    - Permiso: read_patient
    """
    client_ip = request.client.host if request.client else current_user.get("ip_address")

    service = PacienteService(db)
    paciente = service.obtener_paciente(id_paciente)

    if not paciente:
        AuditLogger.log_action(
            user_id=current_user["user_id"],
            action="read_patient",
            resource="paciente",
            resource_id=id_paciente,
            status="failed",
            details={"reason": "not_found"},
            ip_address=client_ip
        )
        raise HTTPException(status_code=404, detail="Paciente no encontrado")

    # Log successful access
    AuditLogger.log_action(
        user_id=current_user["user_id"],
        action="read_patient",
        resource="paciente",
        resource_id=id_paciente,
        status="success",
        ip_address=client_ip
    )

    return paciente


@router.put(
    "/{id_paciente}",
    response_model=PacienteRead,
    dependencies=[
        Depends(require_permission("update_patient")),
        Depends(require_write_rate_limit())
    ]
)
async def actualizar_paciente(
        id_paciente: int,
        data: PacienteUpdate,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user),
        request: Request = None
):

    client_ip = request.client.host if request.client else current_user.get("ip_address")

    service = PacienteService(db)
    paciente_actualizado = service.actualizar_paciente(
        id_paciente,
        data.dict(exclude_unset=True)
    )

    if not paciente_actualizado:
        AuditLogger.log_action(
            user_id=current_user["user_id"],
            action="update_patient",
            resource="paciente",
            resource_id=id_paciente,
            status="failed",
            details={"reason": "not_found"},
            ip_address=client_ip
        )
        raise HTTPException(status_code=404, detail="Paciente no encontrado")

    AuditLogger.log_action(
        user_id=current_user["user_id"],
        action="update_patient",
        resource="paciente",
        resource_id=id_paciente,
        status="success",
        details={
            "nombre": data.nombre,
            "email": data.email
        },
        ip_address=client_ip
    )

    return paciente_actualizado


@router.delete(
    "/{id_paciente}",
    response_model=dict,
    dependencies=[
        Depends(require_permission("delete_patient")),
        Depends(require_write_rate_limit())
    ]
)
async def eliminar_paciente(
        id_paciente: int,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user),
        request: Request = None
):
    client_ip = request.client.host if request.client else current_user.get("ip_address")

    service = PacienteService(db)
    eliminado = service.eliminar_paciente(id_paciente)

    if not eliminado:
        AuditLogger.log_action(
            user_id=current_user["user_id"],
            action="delete_patient",
            resource="paciente",
            resource_id=id_paciente,
            status="failed",
            details={"reason": "not_found"},
            ip_address=client_ip
        )
        raise HTTPException(status_code=404, detail="Paciente no encontrado")

    # Log successful deletion
    AuditLogger.log_action(
        user_id=current_user["user_id"],
        action="delete_patient",
        resource="paciente",
        resource_id=id_paciente,
        status="success",
        ip_address=client_ip
    )

    return {"message": "Paciente eliminado correctamente"}


@router.get("/buscar/{numero_identificacion}", response_model=PacienteRead)
async def buscar_paciente_por_cc(
        numero_identificacion: str,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user),
        request: Request = None
):
    """
    Buscar paciente por número de identificación

    Requiere:
    - Autenticación
    - Permiso: read_patient (implícito)
    """
    client_ip = request.client.host if request.client else current_user.get("ip_address")

    service = PacienteService(db)
    paciente = service.buscar_por_cc(numero_identificacion)

    if not paciente:
        AuditLogger.log_action(
            user_id=current_user["user_id"],
            action="search_patient",
            resource="paciente",
            status="failed",
            details={"search_by": "numero_identificacion"},
            ip_address=client_ip
        )
        raise HTTPException(status_code=404, detail="Paciente no encontrado")

    # Log successful search
    AuditLogger.log_action(
        user_id=current_user["user_id"],
        action="search_patient",
        resource="paciente",
        resource_id=paciente.id_paciente,
        status="success",
        details={"search_by": "numero_identificacion"},
        ip_address=client_ip
    )

    return paciente


@router.get(
    "/{id_paciente}/estadisticas",
    response_model=dict,
    dependencies=[Depends(require_permission("read_patient"))]
)
async def obtener_estadisticas_paciente(
        id_paciente: int,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user),
        request: Request = None
):
    """
    Obtener estadísticas completas del paciente
    Incluye: citas, tratamientos, historiales
    """
    from appointments.infrastructure.repository import CitaRepository
    from treatments.infrastructure.repository import TratamientoRepository
    from historials.infrastructure.repository import HistorialRepository

    client_ip = request.client.host if request.client else current_user.get("ip_address")

    # Verify patient exists
    service = PacienteService(db)
    paciente = service.obtener_paciente(id_paciente)

    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")

    # Get repositories
    cita_repo = CitaRepository(db)
    trat_repo = TratamientoRepository(db)
    hist_repo = HistorialRepository(db)

    # Get data
    citas = cita_repo.get_by_paciente(id_paciente)
    tratamientos = trat_repo.get_by_paciente(db, id_paciente)
    historiales = hist_repo.get_historiales_paciente(id_paciente)

    # Calculate stats
    stats = {
        "id_paciente": id_paciente,
        "nombre_completo": f"{paciente.nombre} {paciente.apellido}",
        "citas": {
            "total": len(citas),
            "por_estado": {}
        },
        "tratamientos": {
            "total": len(tratamientos),
            "activos": len([t for t in tratamientos if t.estado == "Activo"]),
            "completados": len([t for t in tratamientos if t.estado == "Completado"])
        },
        "historiales": {
            "total": len(historiales)
        }
    }

    # Count citas by state
    for cita in citas:
        estado = cita.estado
        if estado not in stats["citas"]["por_estado"]:
            stats["citas"]["por_estado"][estado] = 0
        stats["citas"]["por_estado"][estado] += 1

    # Log access
    AuditLogger.log_action(
        user_id=current_user["user_id"],
        action="read_patient_statistics",
        resource="paciente",
        resource_id=id_paciente,
        status="success",
        ip_address=client_ip
    )

    return stats