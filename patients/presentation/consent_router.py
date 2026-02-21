"""
Router para gestión de Consentimientos de Pacientes.

Cualquier usuario con permiso read_patient / create_patient puede operar.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from typing import List

from shared.database import get_db
from shared.dependencies import (
    get_current_user,
    require_permission,
    require_write_rate_limit,
)
from shared.security_utils import AuditLogger
from patients.application.consent_use_cases import ConsentimientoService
from patients.presentation.consent_schemas import (
    ConsentimientoCreate,
    ConsentimientoUpdate,
    ConsentimientoRead,
    ConsentimientoResumen,
    TiposConsentimientoResponse,
    TIPOS_CONSENTIMIENTO_VALIDOS,
)

router = APIRouter(prefix="/consentimientos", tags=["Consentimientos de Pacientes"])


@router.get(
    "/tipos",
    response_model=TiposConsentimientoResponse,
    dependencies=[Depends(require_permission("read_patient"))],
)
async def listar_tipos_consentimiento(
    current_user: dict = Depends(get_current_user),
):

    return TiposConsentimientoResponse(tipos=TIPOS_CONSENTIMIENTO_VALIDOS)



@router.post(
    "/",
    response_model=ConsentimientoRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[
        Depends(require_permission("create_patient")),
        Depends(require_write_rate_limit()),
    ],
)
async def registrar_consentimiento(
    data: ConsentimientoCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    request: Request = None,
):

    client_ip = request.client.host if request and request.client else current_user.get("ip_address")

    try:
        service = ConsentimientoService(db)
        nuevo = service.crear_consentimiento(
            id_paciente=data.id_paciente,
            tipo_consentimiento=data.tipo_consentimiento,
            url_archivo=data.url_archivo,
            nombre_archivo=data.nombre_archivo,
            tipo_archivo=data.tipo_archivo,
            observaciones=data.observaciones,
            subido_por=current_user["user_id"],
        )

        AuditLogger.log_action(
            user_id=current_user["user_id"],
            action="create_consentimiento",
            resource="consentimiento",
            resource_id=nuevo.id_consentimiento,
            status="success",
            details={
                "id_paciente": data.id_paciente,
                "tipo": data.tipo_consentimiento,
                "archivo": data.nombre_archivo,
            },
            ip_address=client_ip,
        )
        return nuevo

    except HTTPException:
        raise
    except Exception as e:
        AuditLogger.log_action(
            user_id=current_user["user_id"],
            action="create_consentimiento",
            resource="consentimiento",
            status="failed",
            details={"error": str(e)},
            ip_address=client_ip,
        )
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/paciente/{id_paciente}",
    response_model=List[ConsentimientoResumen],
    dependencies=[Depends(require_permission("read_patient"))],
)
async def listar_consentimientos_paciente(
    id_paciente: int,
    solo_activos: bool = True,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    request: Request = None,
):

    if id_paciente < 1:
        raise HTTPException(status_code=400, detail="ID de paciente inválido")

    client_ip = request.client.host if request and request.client else current_user.get("ip_address")

    service = ConsentimientoService(db)
    consentimientos = service.listar_consentimientos_paciente(id_paciente, solo_activos)

    AuditLogger.log_action(
        user_id=current_user["user_id"],
        action="list_consentimientos_paciente",
        resource="consentimiento",
        resource_id=id_paciente,
        status="success",
        details={"count": len(consentimientos), "solo_activos": solo_activos},
        ip_address=client_ip,
    )
    return consentimientos


@router.get(
    "/{id_consentimiento}",
    response_model=ConsentimientoRead,
    dependencies=[Depends(require_permission("read_patient"))],
)
async def obtener_consentimiento(
    id_consentimiento: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    request: Request = None,
):

    client_ip = request.client.host if request and request.client else current_user.get("ip_address")

    service = ConsentimientoService(db)
    c = service.obtener_consentimiento(id_consentimiento)

    AuditLogger.log_action(
        user_id=current_user["user_id"],
        action="read_consentimiento",
        resource="consentimiento",
        resource_id=id_consentimiento,
        status="success",
        ip_address=client_ip,
    )
    return c


@router.patch(
    "/{id_consentimiento}",
    response_model=ConsentimientoRead,
    dependencies=[
        Depends(require_permission("update_patient")),
        Depends(require_write_rate_limit()),
    ],
)
async def actualizar_observaciones(
    id_consentimiento: int,
    data: ConsentimientoUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    request: Request = None,
):

    client_ip = request.client.host if request and request.client else current_user.get("ip_address")

    try:
        service = ConsentimientoService(db)
        actualizado = service.actualizar_observaciones(
            id_consentimiento, data.observaciones or ""
        )

        AuditLogger.log_action(
            user_id=current_user["user_id"],
            action="update_consentimiento",
            resource="consentimiento",
            resource_id=id_consentimiento,
            status="success",
            ip_address=client_ip,
        )
        return actualizado

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete(
    "/{id_consentimiento}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[
        Depends(require_permission("delete_patient")),
        Depends(require_write_rate_limit()),
    ],
)
async def eliminar_consentimiento(
    id_consentimiento: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    request: Request = None,
):
    client_ip = request.client.host if request and request.client else current_user.get("ip_address")

    service = ConsentimientoService(db)
    service.eliminar_consentimiento(id_consentimiento)

    AuditLogger.log_action(
        user_id=current_user["user_id"],
        action="delete_consentimiento",
        resource="consentimiento",
        resource_id=id_consentimiento,
        status="success",
        ip_address=client_ip,
    )
    return None