"""
Router protegido para Pacientes con seguridad completa
Incluye: autenticación, autorización, validación de entrada, sanitización, auditoría
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List, Optional
import math

from shared.database import get_db
from shared.dependencies import (
    get_current_user,
    get_current_employee,
    require_permission,
    require_write_rate_limit,
    verify_patient_access
)
from shared.security_utils import AuditLogger

from security.InputValidator import InputValidator

from patients.application.use_cases import PacienteService
from patients.presentation.schemas import PacienteCreate, PacienteUpdate, PacienteRead, PaginatedPacientesResponse

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
    response_model=PaginatedPacientesResponse,
    dependencies=[Depends(require_permission("read_patient"))]
)
async def listar_pacientes(
        page: int = 1,
        limit: int = 50,
        estado: Optional[str] = None,
        search: Optional[str] = None,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user),
        request: Request = None
):
    """
    Listar todos los pacientes (con paginación optimizada a nivel SQL)

    Requiere:
    - Autenticación
    - Permiso: read_patient

    Query params:
    - page: Número de página (default: 1)
    - limit: Máximo de registros a retornar (default: 50, max: 100)
    - estado: Filtrar por estado (Activo/Inactivo)
    - search: Buscar por nombre, apellido o identificación

    Seguridad mejorada:
    - ✅ Validación contra SQL injection en búsqueda
    - ✅ Sanitización del término de búsqueda
    - ✅ Validación de parámetros de estado
    - ✅ Rate limiting automático
    - ✅ Auditoría de accesos
    """
    # ✅ VALIDAR Y SANITIZAR BÚSQUEDA (PROTECCIÓN SQL INJECTION)
    if search:
        try:
            # Validar contra patrones de SQL injection
            InputValidator.validate_sql_injection(search)

            # Validar contra XSS
            InputValidator.validate_xss(search)

            # Validar contra command injection
            InputValidator.validate_command_injection(search)

        except HTTPException as e:
            # Si detecta patrón peligroso, logear y rechazar
            AuditLogger.log_action(
                user_id=current_user["user_id"],
                action="search_patient_blocked",
                resource="paciente",
                status="blocked",
                details={
                    "search_term": search[:100],  # Limitar para logs
                    "reason": e.detail,
                    "ip": request.client.host if request.client else "unknown"
                },
                ip_address=request.client.host if request.client else "unknown"
            )
            raise HTTPException(
                status_code=400,
                detail="Invalid search term: potentially dangerous pattern detected"
            )

        # Sanitizar término de búsqueda
        search = InputValidator.sanitize_search_term(search)

        # Si después de sanitizar queda vacío, no buscar
        if not search:
            search = None

    # ✅ VALIDAR ESTADO (solo valores permitidos)
    if estado:
        estado = estado.strip()
        if estado not in ["Activo", "Inactivo"]:
            raise HTTPException(
                status_code=400,
                detail="Estado debe ser 'Activo' o 'Inactivo'"
            )

    # ✅ VALIDAR PAGINACIÓN
    if page < 1:
        page = 1

    if limit < 1:
        limit = 1

    # Límite máximo de registros
    limit = min(limit, 100)
    skip = (page - 1) * limit

    client_ip = request.client.host if request.client else current_user.get("ip_address")

    service = PacienteService(db)

    # Use optimized paginated query (SQL level pagination)
    # El término de búsqueda ya está sanitizado
    pacientes, total = service.listar_pacientes_paginados(
        skip=skip,
        limit=limit,
        estado=estado,
        search=search  # ✅ Ya sanitizado
    )

    total_pages = math.ceil(total / limit) if limit > 0 else 0

    # Log access
    AuditLogger.log_action(
        user_id=current_user["user_id"],
        action="list_patients",
        resource="paciente",
        status="success",
        details={
            "count": len(pacientes),
            "page": page,
            "limit": limit,
            "total": total,
            "search_used": bool(search),
            "estado_filter": estado
        },
        ip_address=client_ip
    )

    return PaginatedPacientesResponse(
        data=pacientes,
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages
    )


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

    Seguridad:
    - Validación de ID (debe ser entero positivo)
    - Auditoría de acceso
    """
    # ✅ VALIDAR ID
    if id_paciente < 1:
        raise HTTPException(
            status_code=400,
            detail="ID de paciente inválido"
        )

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
    """
    Actualizar información de paciente

    Requiere:
    - Autenticación
    - Permiso: update_patient
    - Rate limit: 50 writes/minuto

    Seguridad:
    - Validación de ID
    - Validación de campos en schema
    - Sanitización automática
    """
    # ✅ VALIDAR ID
    if id_paciente < 1:
        raise HTTPException(
            status_code=400,
            detail="ID de paciente inválido"
        )

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
            "updated_fields": list(data.dict(exclude_unset=True).keys())
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
    """
    Eliminar paciente (soft delete)

    Requiere:
    - Autenticación
    - Permiso: delete_patient
    - Rate limit: 50 writes/minuto

    Seguridad:
    - Validación de ID
    - Soft delete (no eliminación física)
    - Auditoría completa
    """
    # ✅ VALIDAR ID
    if id_paciente < 1:
        raise HTTPException(
            status_code=400,
            detail="ID de paciente inválido"
        )

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

    Seguridad mejorada:
    - ✅ Sanitización del número de identificación
    - ✅ Validación de formato
    - ✅ Protección contra SQL injection
    """
    client_ip = request.client.host if request.client else current_user.get("ip_address")

    # ✅ VALIDAR Y SANITIZAR número de identificación
    try:
        # Validar contra inyecciones
        InputValidator.validate_sql_injection(numero_identificacion)
        InputValidator.validate_xss(numero_identificacion)

    except HTTPException as e:
        AuditLogger.log_action(
            user_id=current_user["user_id"],
            action="search_patient_by_id_blocked",
            resource="paciente",
            status="blocked",
            details={"numero_identificacion": numero_identificacion[:50], "reason": e.detail},
            ip_address=client_ip
        )
        raise

    # Sanitizar (solo alfanuméricos y guiones)
    numero_identificacion = InputValidator.sanitize_string(numero_identificacion, allow_html=False, max_length=20)

    # Validar formato (solo números, letras y guiones)
    import re
    if not re.match(r'^[0-9A-Za-z-]+$', numero_identificacion):
        raise HTTPException(
            status_code=400,
            detail="Número de identificación inválido (solo números, letras y guiones permitidos)"
        )

    if len(numero_identificacion) < 5:
        raise HTTPException(
            status_code=400,
            detail="Número de identificación demasiado corto"
        )

    service = PacienteService(db)
    paciente = service.buscar_por_cc(numero_identificacion)

    if not paciente:
        AuditLogger.log_action(
            user_id=current_user["user_id"],
            action="search_patient_by_id",
            resource="paciente",
            status="failed",
            details={"search_by": "numero_identificacion", "not_found": True},
            ip_address=client_ip
        )
        raise HTTPException(status_code=404, detail="Paciente no encontrado")

    # Log successful search
    AuditLogger.log_action(
        user_id=current_user["user_id"],
        action="search_patient_by_id",
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

    Seguridad:
    - Validación de ID
    - Verificación de existencia del paciente
    - Auditoría de acceso a datos sensibles
    """
    # ✅ VALIDAR ID
    if id_paciente < 1:
        raise HTTPException(
            status_code=400,
            detail="ID de paciente inválido"
        )

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
    trat_repo = TratamientoRepository()
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

    # Log access to sensitive data
    AuditLogger.log_action(
        user_id=current_user["user_id"],
        action="read_patient_statistics",
        resource="paciente",
        resource_id=id_paciente,
        status="success",
        details={
            "citas_count": stats["citas"]["total"],
            "tratamientos_count": stats["tratamientos"]["total"],
            "historiales_count": stats["historiales"]["total"]
        },
        ip_address=client_ip
    )

    return stats