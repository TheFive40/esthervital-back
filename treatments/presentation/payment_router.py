from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from shared.database import get_db
from shared.dependencies import (
    get_current_user,
    require_permission,
    require_write_rate_limit,
)
from shared.security_utils import AuditLogger
from treatments.application.payment_use_cases import (
    CostoTratamientoService,
    MEDIOS_PAGO_VALIDOS,
)
from treatments.presentation.payment_schemas import (
    AbonoCreate,
    AbonoCreateResponse,
    AbonoRead,
    CostoCreate,
    CostoRead,
    CostoUpdate,
    MediosPagoResponse,
    ResumenFinanciero,
)

router = APIRouter(prefix="/pagos", tags=["Pagos y Abonos de Tratamientos"])


# ── Catálogos ─────────────────────────────────────────────────────────────────

@router.get(
    "/medios-pago",
    response_model=MediosPagoResponse,
    dependencies=[Depends(require_permission("read_treatment"))],
)
async def listar_medios_pago():
    """Lista los medios de pago disponibles."""
    return MediosPagoResponse(medios=MEDIOS_PAGO_VALIDOS)


# ── Costos ────────────────────────────────────────────────────────────────────

@router.post(
    "/costos/",
    response_model=CostoRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[
        Depends(require_permission("create_treatment")),
        Depends(require_write_rate_limit()),
    ],
)
async def registrar_costo(
    data: CostoCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    request: Request = None,
):
    """
    Registra el costo total de un tratamiento.

    **Nota:** Si ya enviaste `costo_total` al crear el tratamiento (`POST /tratamientos/`),
    no es necesario usar este endpoint. Úsalo solo si olvidaste incluirlo al crear
    o necesitas registrar el costo de un tratamiento existente.
    """
    client_ip = request.client.host if request and request.client else current_user.get("ip_address")

    try:
        service = CostoTratamientoService(db)
        nuevo = service.registrar_costo(
            id_tratamiento=data.id_tratamiento,
            costo_total=data.costo_total,
            notas=data.notas,
            registrado_por=current_user["user_id"],
        )

        AuditLogger.log_action(
            user_id=current_user["user_id"],
            action="create_costo_tratamiento",
            resource="costo_tratamiento",
            resource_id=nuevo.id_costo,
            status="success",
            details={"id_tratamiento": data.id_tratamiento, "costo_total": str(data.costo_total)},
            ip_address=client_ip,
        )
        return nuevo

    except HTTPException:
        raise
    except Exception as e:
        AuditLogger.log_action(
            user_id=current_user["user_id"],
            action="create_costo_tratamiento",
            resource="costo_tratamiento",
            status="failed",
            details={"error": str(e)},
            ip_address=client_ip,
        )
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/costos/tratamiento/{id_tratamiento}",
    response_model=CostoRead,
    dependencies=[Depends(require_permission("read_treatment"))],
)
async def obtener_costo_tratamiento(
    id_tratamiento: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    request: Request = None,
):
    """Obtiene el costo registrado de un tratamiento."""
    client_ip = request.client.host if request and request.client else current_user.get("ip_address")
    service = CostoTratamientoService(db)
    costo = service.obtener_costo_tratamiento(id_tratamiento)

    AuditLogger.log_action(
        user_id=current_user["user_id"],
        action="read_costo_tratamiento",
        resource="costo_tratamiento",
        resource_id=id_tratamiento,
        status="success",
        ip_address=client_ip,
    )
    return costo


@router.get(
    "/costos/tratamiento/{id_tratamiento}/resumen",
    response_model=ResumenFinanciero,
    dependencies=[Depends(require_permission("read_treatment"))],
)
async def resumen_financiero_tratamiento(
    id_tratamiento: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    request: Request = None,
):
    """
    Resumen financiero del tratamiento:
    - Costo total pactado
    - Total abonado (suma de abonos confirmados)
    - Saldo pendiente
    - Estado de pago: Pendiente / Abono parcial / Pagado
    """
    client_ip = request.client.host if request and request.client else current_user.get("ip_address")
    service = CostoTratamientoService(db)
    resumen = service.resumen_financiero(id_tratamiento)

    AuditLogger.log_action(
        user_id=current_user["user_id"],
        action="read_resumen_financiero",
        resource="costo_tratamiento",
        resource_id=id_tratamiento,
        status="success",
        ip_address=client_ip,
    )
    return resumen


@router.put(
    "/costos/tratamiento/{id_tratamiento}",
    response_model=CostoRead,
    dependencies=[
        Depends(require_permission("update_treatment")),
        Depends(require_write_rate_limit()),
    ],
)
async def actualizar_costo_tratamiento(
    id_tratamiento: int,
    data: CostoUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    request: Request = None,
):
    """
    Actualiza el costo total pactado para un tratamiento.
    Útil para aplicar descuentos o corregir errores de registro.
    Los abonos ya registrados no se eliminan.
    """
    client_ip = request.client.host if request and request.client else current_user.get("ip_address")

    try:
        service = CostoTratamientoService(db)
        actualizado = service.actualizar_costo(
            id_tratamiento=id_tratamiento,
            nuevo_costo_total=data.costo_total,
            notas=data.notas,
        )

        AuditLogger.log_action(
            user_id=current_user["user_id"],
            action="update_costo_tratamiento",
            resource="costo_tratamiento",
            resource_id=id_tratamiento,
            status="success",
            details={"nuevo_costo": str(data.costo_total)},
            ip_address=client_ip,
        )
        return actualizado

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Abonos ────────────────────────────────────────────────────────────────────

@router.post(
    "/abonos/",
    response_model=AbonoCreateResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[
        Depends(require_permission("create_treatment")),
        Depends(require_write_rate_limit()),
    ],
)
async def registrar_abono(
    data: AbonoCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    request: Request = None,
):
    """
    Registra un abono (pago parcial) a un tratamiento.

    La respuesta incluye el `resumen_financiero` actualizado con el nuevo
    saldo pendiente, para que el frontend pueda actualizar la UI sin necesidad
    de hacer otra petición.
    """
    client_ip = request.client.host if request and request.client else current_user.get("ip_address")

    try:
        service = CostoTratamientoService(db)
        fecha_pago = data.fecha_pago or datetime.utcnow()

        abono = service.registrar_abono(
            id_tratamiento=data.id_tratamiento,
            monto=data.monto,
            medio_pago=data.medio_pago,
            fecha_pago=fecha_pago,
            referencia=data.referencia,
            notas=data.notas,
            registrado_por=current_user["user_id"],
        )

        excede = getattr(abono, "_excede_saldo", False)
        advertencia = (
            "El abono supera el saldo pendiente del tratamiento. Verifique si es correcto."
            if excede else None
        )

        # Obtener resumen financiero actualizado
        resumen = service.resumen_financiero(data.id_tratamiento)

        AuditLogger.log_action(
            user_id=current_user["user_id"],
            action="create_abono_tratamiento",
            resource="abono_tratamiento",
            resource_id=abono.id_abono,
            status="success",
            details={
                "id_tratamiento": data.id_tratamiento,
                "monto": str(data.monto),
                "medio_pago": data.medio_pago,
                "saldo_pendiente_nuevo": resumen["saldo_pendiente"],
            },
            ip_address=client_ip,
        )

        return AbonoCreateResponse(
            id_abono=abono.id_abono,
            id_costo=abono.id_costo,
            monto=abono.monto,
            medio_pago=abono.medio_pago,
            referencia=abono.referencia,
            estado=abono.estado,
            fecha_pago=abono.fecha_pago,
            notas=abono.notas,
            fecha_registro=abono.fecha_registro,
            registrado_por=abono.registrado_por,
            resumen_financiero=resumen,
            advertencia=advertencia,
        )

    except HTTPException:
        raise
    except Exception as e:
        AuditLogger.log_action(
            user_id=current_user["user_id"],
            action="create_abono_tratamiento",
            resource="abono_tratamiento",
            status="failed",
            details={"error": str(e)},
            ip_address=client_ip,
        )
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/abonos/tratamiento/{id_tratamiento}",
    response_model=List[AbonoRead],
    dependencies=[Depends(require_permission("read_treatment"))],
)
async def listar_abonos_tratamiento(
    id_tratamiento: int,
    solo_confirmados: bool = False,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    request: Request = None,
):
    """
    Lista todos los abonos de un tratamiento.
    Usa `solo_confirmados=true` para excluir abonos anulados.
    """
    client_ip = request.client.host if request and request.client else current_user.get("ip_address")

    service = CostoTratamientoService(db)
    abonos = service.listar_abonos(id_tratamiento, solo_confirmados)

    AuditLogger.log_action(
        user_id=current_user["user_id"],
        action="list_abonos_tratamiento",
        resource="abono_tratamiento",
        resource_id=id_tratamiento,
        status="success",
        details={"count": len(abonos), "solo_confirmados": solo_confirmados},
        ip_address=client_ip,
    )
    return abonos


@router.delete(
    "/abonos/{id_abono}/anular",
    response_model=AbonoRead,
    dependencies=[
        Depends(require_permission("update_treatment")),
        Depends(require_write_rate_limit()),
    ],
)
async def anular_abono(
    id_abono: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    request: Request = None,
):
    """
    Anula un abono. El registro permanece en BD con estado `Anulado`
    y ya no se contabiliza en el saldo pagado.
    """
    client_ip = request.client.host if request and request.client else current_user.get("ip_address")

    try:
        service = CostoTratamientoService(db)
        abono_anulado = service.anular_abono(id_abono)

        AuditLogger.log_action(
            user_id=current_user["user_id"],
            action="anular_abono_tratamiento",
            resource="abono_tratamiento",
            resource_id=id_abono,
            status="success",
            ip_address=client_ip,
        )
        return abono_anulado

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))