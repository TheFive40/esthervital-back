from sqlalchemy.orm import Session
from sqlalchemy import desc
from patients.infrastructure.consent_models import ConsentimientoPaciente
from typing import Optional, List


class ConsentimientoRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, consentimiento: ConsentimientoPaciente) -> ConsentimientoPaciente:
        self.db.add(consentimiento)
        self.db.commit()
        self.db.refresh(consentimiento)
        return consentimiento

    def get_by_id(self, id_consentimiento: int) -> Optional[ConsentimientoPaciente]:
        return (
            self.db.query(ConsentimientoPaciente)
            .filter(ConsentimientoPaciente.id_consentimiento == id_consentimiento)
            .first()
        )

    def get_by_paciente(
        self,
        id_paciente: int,
        solo_activos: bool = True
    ) -> List[ConsentimientoPaciente]:
        query = self.db.query(ConsentimientoPaciente).filter(
            ConsentimientoPaciente.id_paciente == id_paciente
        )
        if solo_activos:
            query = query.filter(ConsentimientoPaciente.activo == True)
        return query.order_by(desc(ConsentimientoPaciente.fecha_subida)).all()

    def get_paginated(
        self,
        id_paciente: Optional[int] = None,
        skip: int = 0,
        limit: int = 50
    ) -> tuple[List[ConsentimientoPaciente], int]:
        query = self.db.query(ConsentimientoPaciente).filter(
            ConsentimientoPaciente.activo == True
        )
        if id_paciente:
            query = query.filter(ConsentimientoPaciente.id_paciente == id_paciente)

        total = query.count()
        items = query.order_by(desc(ConsentimientoPaciente.fecha_subida)).offset(skip).limit(limit).all()
        return items, total

    def soft_delete(self, consentimiento: ConsentimientoPaciente) -> ConsentimientoPaciente:
        consentimiento.activo = False
        self.db.commit()
        self.db.refresh(consentimiento)
        return consentimiento

    def update(self, consentimiento: ConsentimientoPaciente) -> ConsentimientoPaciente:
        self.db.commit()
        self.db.refresh(consentimiento)
        return consentimiento