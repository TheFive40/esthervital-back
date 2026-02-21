"""
Casos de uso para la gestión de costos y abonos de tratamientos.
"""

from decimal import Decimal
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from treatments.infrastructure.payment_models import CostoTratamiento, AbonoTratamiento
from treatments.infrastructure.payment_repository import (
    CostoTratamientoRepository,
    AbonoRepository,
)

MEDIOS_PAGO_VALIDOS = [
    "Efectivo",
    "Transferencia bancaria",
    "Tarjeta débito",
    "Tarjeta crédito",
    "Nequi",
    "Daviplata",
    "Otro",
]


class CostoTratamientoService:
    def __init__(self, db: Session):
        self.costo_repo = CostoTratamientoRepository(db)
        self.abono_repo = AbonoRepository(db)


    def registrar_costo(
        self,
        id_tratamiento: int,
        costo_total: Decimal,
        notas: Optional[str],
        registrado_por: Optional[int],
    ) -> CostoTratamiento:
        """
        Registra el costo total acordado para un tratamiento.
        Solo puede haber un costo por tratamiento (unicidad forzada en BD).
        """
        existente = self.costo_repo.get_by_tratamiento(id_tratamiento)
        if existente:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Este tratamiento ya tiene un costo registrado. "
                    "Use el endpoint de actualización para modificarlo."
                ),
            )

        if costo_total <= 0:
            raise HTTPException(
                status_code=400,
                detail="El costo total debe ser mayor a cero."
            )

        costo = CostoTratamiento(
            id_tratamiento=id_tratamiento,
            costo_total=costo_total,
            notas=notas,
            registrado_por=registrado_por,
        )
        return self.costo_repo.create(costo)

    def obtener_costo_tratamiento(self, id_tratamiento: int) -> CostoTratamiento:
        costo = self.costo_repo.get_by_tratamiento(id_tratamiento)
        if not costo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No se encontró información de costo para este tratamiento.",
            )
        return costo

    def obtener_costo_por_id(self, id_costo: int) -> CostoTratamiento:
        costo = self.costo_repo.get_by_id(id_costo)
        if not costo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Registro de costo no encontrado.",
            )
        return costo

    def actualizar_costo(
        self,
        id_tratamiento: int,
        nuevo_costo_total: Decimal,
        notas: Optional[str],
    ) -> CostoTratamiento:

        costo = self.obtener_costo_tratamiento(id_tratamiento)

        if nuevo_costo_total <= 0:
            raise HTTPException(status_code=400, detail="El costo total debe ser mayor a cero.")

        costo.costo_total = nuevo_costo_total
        if notas is not None:
            costo.notas = notas

        return self.costo_repo.update(costo)

    def resumen_financiero(self, id_tratamiento: int) -> dict:

        costo = self.obtener_costo_tratamiento(id_tratamiento)
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
            "id_tratamiento": id_tratamiento,
            "costo_total": total,
            "total_abonado": abonado,
            "saldo_pendiente": max(saldo, 0),  # No mostrar negativos
            "estado_pago": estado_pago,
            "cantidad_abonos": len([a for a in costo.abonos if a.estado == "Confirmado"]),
        }


    def registrar_abono(
        self,
        id_tratamiento: int,
        monto: Decimal,
        medio_pago: str,
        fecha_pago,
        referencia: Optional[str],
        notas: Optional[str],
        registrado_por: Optional[int],
    ) -> AbonoTratamiento:
        """
        Registra un pago parcial (abono) al tratamiento.
        Valida que el costo esté registrado y que el monto sea positivo.
        """
        costo = self.obtener_costo_tratamiento(id_tratamiento)

        if monto <= 0:
            raise HTTPException(status_code=400, detail="El monto del abono debe ser mayor a cero.")

        if medio_pago not in MEDIOS_PAGO_VALIDOS:
            raise HTTPException(
                status_code=400,
                detail=f"Medio de pago inválido. Opciones: {', '.join(MEDIOS_PAGO_VALIDOS)}",
            )

        saldo = costo.saldo_pendiente
        excede = float(monto) > saldo and saldo > 0

        abono = AbonoTratamiento(
            id_costo=costo.id_costo,
            monto=monto,
            medio_pago=medio_pago,
            referencia=referencia,
            notas=notas,
            fecha_pago=fecha_pago,
            estado="Confirmado",
            registrado_por=registrado_por,
        )
        abono_creado = self.abono_repo.create(abono)

        abono_creado._excede_saldo = excede
        return abono_creado

    def anular_abono(self, id_abono: int) -> AbonoTratamiento:
        abono = self.abono_repo.get_by_id(id_abono)
        if not abono:
            raise HTTPException(status_code=404, detail="Abono no encontrado.")
        if abono.estado == "Anulado":
            raise HTTPException(status_code=400, detail="El abono ya está anulado.")

        abono.estado = "Anulado"
        return self.abono_repo.update(abono)

    def listar_abonos(
        self, id_tratamiento: int, solo_confirmados: bool = False
    ):
        costo = self.obtener_costo_tratamiento(id_tratamiento)
        return self.abono_repo.get_by_costo(costo.id_costo, solo_confirmados)