"""
Router protegido para Historiales Clínicos
Incluye autenticación, autorización, rate limiting y auditoría
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List

from shared.database import get_db
from shared.dependencies import (
    get_current_user,
    get_current_employee,
    require_permission,
    require_write_rate_limit,
    verify_patient_access
)
from shared.security_utils import AuditLogger

from historials.application.use_cases import HistorialService
from historials.presentation.schemas import (
    HistorialCreate, HistorialRead, HistorialUpdate,
    DocumentoCreate, DocumentoRead
)

router = APIRouter(prefix="/historiales", tags=["Historiales Clínicos"])


# ============ HISTORIALES ENDPOINTS ============

@router.get(
    "/",
    response_model=List[HistorialRead],
    dependencies=[Depends(require_permission("read_historial"))]
)
async def listar_todos_historiales(
        skip: int = 0,
        limit: int = 50,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user),
        request: Request = None
):
    """
    Listar todos los historiales clínicos

    Requiere:
    - Autenticación
    - Permiso: read_historial

    Query params:
    - skip: Número de registros a saltar (default: 0)
    - limit: Máximo de registros a retornar (default: 50, max: 100)
    """
    limit = min(limit, 100)
    client_ip = request.client.host if request.client else current_user.get("ip_address")

    try:
        service = HistorialService(db)
        historiales = service.listar_todos()

        # Apply pagination
        historiales = historiales[skip:skip + limit]

        # Log access
        AuditLogger.log_action(
            user_id=current_user["user_id"],
            action="list_all_historiales",
            resource="historial",
            status="success",
            details={"count": len(historiales), "skip": skip, "limit": limit},
            ip_address=client_ip
        )

        return historiales

    except Exception as e:
        AuditLogger.log_action(
            user_id=current_user["user_id"],
            action="list_all_historiales",
            resource="historial",
            status="failed",
            details={"error": str(e)},
            ip_address=client_ip
        )
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/",
    response_model=HistorialRead,
    dependencies=[
        Depends(require_permission("create_historial")),
        Depends(require_write_rate_limit())
    ]
)
async def crear_historial(
        historial: HistorialCreate,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user),
        request: Request = None
):
    """
    Crear nuevo historial clínico

    Requiere:
    - Autenticación
    - Permiso: create_historial
    - Rate limit: 50 writes/minuto

    Roles permitidos:
    - Administrador
    - Empleado
    """
    client_ip = request.client.host if request.client else current_user.get("ip_address")

    try:
        # Verificar que el paciente existe
        service = HistorialService(db)

        # Crear historial
        nuevo = service.crear_historial(historial.dict())

        # Log successful creation
        AuditLogger.log_action(
            user_id=current_user["user_id"],
            action="create_historial",
            resource="historial",
            resource_id=nuevo.id_historial,
            status="success",
            details={
                "id_paciente": historial.id_paciente,
                "motivo_consulta": historial.motivo_consulta[:50] if historial.motivo_consulta else None
            },
            ip_address=client_ip
        )

        return nuevo

    except Exception as e:
        AuditLogger.log_action(
            user_id=current_user["user_id"],
            action="create_historial",
            resource="historial",
            status="failed",
            details={"error": str(e)},
            ip_address=client_ip
        )
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/paciente/{id_paciente}",
    response_model=List[HistorialRead],
    dependencies=[Depends(require_permission("read_historial"))]
)
async def listar_historiales_paciente(
        id_paciente: int,
        skip: int = 0,
        limit: int = 50,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user),
        request: Request = None
):
    """
    Listar historiales de un paciente específico

    Requiere:
    - Autenticación
    - Permiso: read_historial

    Query params:
    - skip: Número de registros a saltar (default: 0)
    - limit: Máximo de registros a retornar (default: 50, max: 100)
    """
    # Límite máximo de registros
    limit = min(limit, 100)

    client_ip = request.client.host if request.client else current_user.get("ip_address")

    try:
        service = HistorialService(db)
        historiales = service.listar_historiales_paciente(id_paciente)

        # Apply pagination
        historiales = historiales[skip:skip + limit]

        # Log access
        AuditLogger.log_action(
            user_id=current_user["user_id"],
            action="list_historiales_paciente",
            resource="historial",
            resource_id=id_paciente,
            status="success",
            details={"count": len(historiales), "skip": skip, "limit": limit},
            ip_address=client_ip
        )

        return historiales

    except Exception as e:
        AuditLogger.log_action(
            user_id=current_user["user_id"],
            action="list_historiales_paciente",
            resource="historial",
            status="failed",
            details={"error": str(e)},
            ip_address=client_ip
        )
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/{id_historial}",
    response_model=HistorialRead,
    dependencies=[Depends(require_permission("read_historial"))]
)
async def obtener_historial(
        id_historial: int,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user),
        request: Request = None
):
    """
    Obtener detalles de un historial específico

    Requiere:
    - Autenticación
    - Permiso: read_historial
    """
    client_ip = request.client.host if request.client else current_user.get("ip_address")

    service = HistorialService(db)
    historial = service.obtener_historial(id_historial)

    if not historial:
        AuditLogger.log_action(
            user_id=current_user["user_id"],
            action="read_historial",
            resource="historial",
            resource_id=id_historial,
            status="failed",
            details={"reason": "not_found"},
            ip_address=client_ip
        )
        raise HTTPException(status_code=404, detail="Historial no encontrado")

    # Log successful access
    AuditLogger.log_action(
        user_id=current_user["user_id"],
        action="read_historial",
        resource="historial",
        resource_id=id_historial,
        status="success",
        ip_address=client_ip
    )

    return historial


@router.put(
    "/{id_historial}",
    response_model=HistorialRead,
    dependencies=[
        Depends(require_permission("update_historial")),
        Depends(require_write_rate_limit())
    ]
)
async def actualizar_historial(
        id_historial: int,
        data: HistorialUpdate,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user),
        request: Request = None
):
    """
    Actualizar historial clínico

    Requiere:
    - Autenticación
    - Permiso: update_historial
    - Rate limit: 50 writes/minuto
    """
    client_ip = request.client.host if request.client else current_user.get("ip_address")

    service = HistorialService(db)
    historial_actualizado = service.actualizar_historial(
        id_historial,
        data.dict(exclude_unset=True)
    )

    if not historial_actualizado:
        AuditLogger.log_action(
            user_id=current_user["user_id"],
            action="update_historial",
            resource="historial",
            resource_id=id_historial,
            status="failed",
            details={"reason": "not_found"},
            ip_address=client_ip
        )
        raise HTTPException(status_code=404, detail="Historial no encontrado")

    # Log successful update
    AuditLogger.log_action(
        user_id=current_user["user_id"],
        action="update_historial",
        resource="historial",
        resource_id=id_historial,
        status="success",
        details={
            "motivo_consulta": data.motivo_consulta[:50] if data.motivo_consulta else None,
            "diagnostico": data.diagnostico[:50] if data.diagnostico else None
        },
        ip_address=client_ip
    )

    return historial_actualizado


@router.delete(
    "/{id_historial}",
    response_model=dict,
    dependencies=[
        Depends(require_permission("delete_historial")),
        Depends(require_write_rate_limit())
    ]
)
async def eliminar_historial(
        id_historial: int,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user),
        request: Request = None
):
    """
    Eliminar historial clínico

    Requiere:
    - Autenticación
    - Permiso: delete_historial
    - Rate limit: 50 writes/minuto

    Nota: Eliminación lógica (soft delete)
    """
    client_ip = request.client.host if request.client else current_user.get("ip_address")

    service = HistorialService(db)
    eliminado = service.eliminar_historial(id_historial)

    if not eliminado:
        AuditLogger.log_action(
            user_id=current_user["user_id"],
            action="delete_historial",
            resource="historial",
            resource_id=id_historial,
            status="failed",
            details={"reason": "not_found"},
            ip_address=client_ip
        )
        raise HTTPException(status_code=404, detail="Historial no encontrado")

    # Log successful deletion
    AuditLogger.log_action(
        user_id=current_user["user_id"],
        action="delete_historial",
        resource="historial",
        resource_id=id_historial,
        status="success",
        ip_address=client_ip
    )

    return {"message": "Historial eliminado correctamente"}


# ============ DOCUMENTOS ENDPOINTS ============

@router.post(
    "/documentos/",
    response_model=DocumentoRead,
    dependencies=[
        Depends(require_permission("create_historial")),
        Depends(require_write_rate_limit())
    ]
)
async def agregar_documento(
        documento: DocumentoCreate,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user),
        request: Request = None
):
    """
    Agregar documento clínico a un historial

    Requiere:
    - Autenticación
    - Permiso: create_historial
    - Rate limit: 50 writes/minuto

    Documentos soportados:
    - Recetas
    - Análisis de laboratorio
    - Imagenes médicas
    - Formularios
    - Otros
    """
    client_ip = request.client.host if request.client else current_user.get("ip_address")

    try:
        service = HistorialService(db)
        nuevo = service.agregar_documento(documento.dict())

        # Log successful upload
        AuditLogger.log_action(
            user_id=current_user["user_id"],
            action="upload_documento",
            resource="documento",
            resource_id=nuevo.id_documento,
            status="success",
            details={
                "tipo_documento": documento.tipo_documento,
                "id_historial": documento.id_historial
            },
            ip_address=client_ip
        )

        return nuevo

    except Exception as e:
        AuditLogger.log_action(
            user_id=current_user["user_id"],
            action="upload_documento",
            resource="documento",
            status="failed",
            details={"error": str(e)},
            ip_address=client_ip
        )
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/documentos/{id_historial}",
    response_model=List[DocumentoRead],
    dependencies=[Depends(require_permission("read_historial"))]
)
async def listar_documentos_historial(
        id_historial: int,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user),
        request: Request = None
):
    """
    Listar documentos clínicos de un historial

    Requiere:
    - Autenticación
    - Permiso: read_historial

    Retorna:
    - Lista de documentos ordenados por fecha
    """
    client_ip = request.client.host if request.client else current_user.get("ip_address")

    try:
        service = HistorialService(db)
        documentos = service.listar_documentos_historial(id_historial)

        # Log access
        AuditLogger.log_action(
            user_id=current_user["user_id"],
            action="list_documentos",
            resource="documento",
            resource_id=id_historial,
            status="success",
            details={"count": len(documentos)},
            ip_address=client_ip
        )

        return documentos

    except Exception as e:
        AuditLogger.log_action(
            user_id=current_user["user_id"],
            action="list_documentos",
            resource="documento",
            status="failed",
            details={"error": str(e)},
            ip_address=client_ip
        )
        raise HTTPException(status_code=400, detail=str(e))


# ============ ENDPOINTS ADICIONALES ============

@router.get(
    "/{id_historial}/resumen",
    response_model=dict,
    dependencies=[Depends(require_permission("read_historial"))]
)
async def obtener_resumen_historial(
        id_historial: int,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user),
        request: Request = None
):
    """
    Obtener resumen completo del historial
    Incluye: datos básicos, documentos, diagnóstico, tratamiento

    Requiere:
    - Autenticación
    - Permiso: read_historial
    """
    client_ip = request.client.host if request.client else current_user.get("ip_address")

    try:
        service = HistorialService(db)

        # Obtener historial
        historial = service.obtener_historial(id_historial)
        if not historial:
            raise HTTPException(status_code=404, detail="Historial no encontrado")

        # Obtener documentos
        documentos = service.listar_documentos_historial(id_historial)

        # Construir resumen
        resumen = {
            "id_historial": historial.id_historial,
            "id_paciente": historial.id_paciente,
            "motivo_consulta": historial.motivo_consulta,
            "diagnostico": historial.diagnostico,
            "tratamiento": historial.tratamiento,
            "sesiones_planificadas": historial.sesiones_planificadas,
            "fecha_ingreso": historial.fecha_ingreso,
            "documentos": [
                {
                    "id": doc.id_documento,
                    "tipo": doc.tipo_documento,
                    "descripcion": doc.descripcion,
                    "fecha": doc.fecha_subida
                }
                for doc in documentos
            ],
            "total_documentos": len(documentos)
        }

        # Log access
        AuditLogger.log_action(
            user_id=current_user["user_id"],
            action="read_historial_resumen",
            resource="historial",
            resource_id=id_historial,
            status="success",
            ip_address=client_ip
        )

        return resumen

    except HTTPException:
        raise
    except Exception as e:
        AuditLogger.log_action(
            user_id=current_user["user_id"],
            action="read_historial_resumen",
            resource="historial",
            status="failed",
            details={"error": str(e)},
            ip_address=client_ip
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/buscar/motivo/{termino}",
    response_model=List[HistorialRead],
    dependencies=[Depends(require_permission("read_historial"))]
)
async def buscar_por_motivo(
        termino: str,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user),
        request: Request = None
):
    """
    Buscar historiales por motivo de consulta

    Requiere:
    - Autenticación
    - Permiso: read_historial

    Parámetros:
    - termino: Texto a buscar en motivo_consulta
    """
    client_ip = request.client.host if request.client else current_user.get("ip_address")

    try:
        service = HistorialService(db)
        todos_historiales = service.listar_todos()

        # Filtrar por motivo (búsqueda simple en memoria)
        # En producción, usar búsqueda en BD
        resultados = [
            h for h in todos_historiales
            if h.motivo_consulta and termino.lower() in h.motivo_consulta.lower()
        ]

        # Log search
        AuditLogger.log_action(
            user_id=current_user["user_id"],
            action="search_historiales",
            resource="historial",
            status="success",
            details={"termino": termino, "resultados": len(resultados)},
            ip_address=client_ip
        )

        return resultados

    except Exception as e:
        AuditLogger.log_action(
            user_id=current_user["user_id"],
            action="search_historiales",
            resource="historial",
            status="failed",
            details={"error": str(e), "termino": termino},
            ip_address=client_ip
        )
        raise HTTPException(status_code=400, detail=str(e))