from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from treatments.infrastructure.payment_models import CostoTratamiento, AbonoTratamiento
from typing import Optional, List


class CostoTratamientoRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, costo: CostoTratamiento) -> CostoTratamiento:
        self.db.add(costo)
        self.db.commit()
        self.db.refresh(costo)
        return costo

    def get_by_id(self, id_costo: int) -> Optional[CostoTratamiento]:
        return (
            self.db.query(CostoTratamiento)
            .options(joinedload(CostoTratamiento.abonos))
            .filter(CostoTratamiento.id_costo == id_costo)
            .first()
        )

    def get_by_tratamiento(self, id_tratamiento: int) -> Optional[CostoTratamiento]:
        return (
            self.db.query(CostoTratamiento)
            .options(joinedload(CostoTratamiento.abonos))
            .filter(CostoTratamiento.id_tratamiento == id_tratamiento)
            .first()
        )

    def update(self, costo: CostoTratamiento) -> CostoTratamiento:
        self.db.commit()
        self.db.refresh(costo)
        return costo

    def delete(self, costo: CostoTratamiento) -> None:
        self.db.delete(costo)
        self.db.commit()


class AbonoRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, abono: AbonoTratamiento) -> AbonoTratamiento:
        self.db.add(abono)
        self.db.commit()
        self.db.refresh(abono)
        return abono

    def get_by_id(self, id_abono: int) -> Optional[AbonoTratamiento]:
        return (
            self.db.query(AbonoTratamiento)
            .filter(AbonoTratamiento.id_abono == id_abono)
            .first()
        )

    def get_by_costo(
        self,
        id_costo: int,
        solo_confirmados: bool = False
    ) -> List[AbonoTratamiento]:
        query = self.db.query(AbonoTratamiento).filter(
            AbonoTratamiento.id_costo == id_costo
        )
        if solo_confirmados:
            query = query.filter(AbonoTratamiento.estado == "Confirmado")
        return query.order_by(desc(AbonoTratamiento.fecha_pago)).all()

    def update(self, abono: AbonoTratamiento) -> AbonoTratamiento:
        self.db.commit()
        self.db.refresh(abono)
        return abono