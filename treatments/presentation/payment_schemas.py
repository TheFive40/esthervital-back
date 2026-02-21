"""
Schemas Pydantic para Costos y Abonos de Tratamientos.
"""

from pydantic import BaseModel, validator
from decimal import Decimal
from typing import Optional, List
from datetime import datetime

from treatments.application.payment_use_cases import MEDIOS_PAGO_VALIDOS


# ──────────────────────────────────────────────────────────
# COSTO TOTAL
# ──────────────────────────────────────────────────────────

class CostoCreate(BaseModel):
    id_tratamiento: int
    costo_total: Decimal
    notas: Optional[str] = None

    @validator("costo_total")
    def validate_costo(cls, v):
        if v <= 0:
            raise ValueError("El costo total debe ser mayor a cero.")
        if v > Decimal("999_999_999.99"):
            raise ValueError("El costo total supera el límite permitido.")
        return round(v, 2)

    @validator("id_tratamiento")
    def validate_id(cls, v):
        if v < 1:
            raise ValueError("ID de tratamiento inválido.")
        return v

    @validator("notas")
    def validate_notas(cls, v):
        if v and len(v) > 500:
            raise ValueError("Las notas no pueden superar 500 caracteres.")
        return v


class CostoUpdate(BaseModel):
    costo_total: Decimal
    notas: Optional[str] = None

    @validator("costo_total")
    def validate_costo(cls, v):
        if v <= 0:
            raise ValueError("El costo total debe ser mayor a cero.")
        return round(v, 2)


class CostoRead(BaseModel):
    id_costo: int
    id_tratamiento: int
    costo_total: Decimal
    notas: Optional[str]
    fecha_registro: datetime
    registrado_por: Optional[int]

    class Config:
        from_attributes = True


class ResumenFinanciero(BaseModel):
    """Resumen financiero de un tratamiento: costo, abonos y saldo."""
    id_costo: int
    id_tratamiento: int
    costo_total: float
    total_abonado: float
    saldo_pendiente: float
    estado_pago: str          # "Pendiente" | "Abono parcial" | "Pagado"
    cantidad_abonos: int


# ──────────────────────────────────────────────────────────
# ABONOS
# ──────────────────────────────────────────────────────────

class AbonoCreate(BaseModel):
    """
    Datos para registrar un abono (pago parcial) a un tratamiento.
    """
    id_tratamiento: int
    monto: Decimal
    medio_pago: str
    fecha_pago: Optional[datetime] = None   # Si no se envía, se usa NOW()
    referencia: Optional[str] = None
    notas: Optional[str] = None

    @validator("id_tratamiento")
    def validate_id(cls, v):
        if v < 1:
            raise ValueError("ID de tratamiento inválido.")
        return v

    @validator("monto")
    def validate_monto(cls, v):
        if v <= 0:
            raise ValueError("El monto del abono debe ser mayor a cero.")
        if v > Decimal("999_999_999.99"):
            raise ValueError("El monto supera el límite permitido.")
        return round(v, 2)

    @validator("medio_pago")
    def validate_medio_pago(cls, v):
        if v not in MEDIOS_PAGO_VALIDOS:
            raise ValueError(
                f"Medio de pago inválido. Opciones: {', '.join(MEDIOS_PAGO_VALIDOS)}"
            )
        return v

    @validator("referencia")
    def validate_referencia(cls, v):
        if v and len(v) > 100:
            raise ValueError("La referencia no puede superar 100 caracteres.")
        return v

    @validator("notas")
    def validate_notas(cls, v):
        if v and len(v) > 500:
            raise ValueError("Las notas no pueden superar 500 caracteres.")
        return v


class AbonoRead(BaseModel):
    id_abono: int
    id_costo: int
    monto: Decimal
    medio_pago: str
    referencia: Optional[str]
    estado: str
    fecha_pago: datetime
    notas: Optional[str]
    fecha_registro: datetime
    registrado_por: Optional[int]

    class Config:
        from_attributes = True


class AbonoCreateResponse(AbonoRead):
    """Igual que AbonoRead pero incluye advertencia si el abono excede el saldo."""
    advertencia: Optional[str] = None


class MediosPagoResponse(BaseModel):
    medios: List[str]