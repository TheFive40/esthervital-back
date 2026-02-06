from sqlalchemy.orm import Session
from sqlalchemy import or_, desc
from appointments.infrastructure.models import Cita
from typing import Optional
from datetime import date

class CitaRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, cita: Cita) -> Cita:
        self.db.add(cita)
        self.db.commit()
        self.db.refresh(cita)
        return cita

    def get_by_id(self, id_cita: int) -> Cita | None:
        return self.db.query(Cita).filter(Cita.id_cita == id_cita).first()

    def get_all(self) -> list[Cita]:
        """Returns all appointments - use get_paginated for large datasets"""
        return self.db.query(Cita).all()

    def get_paginated(
        self,
        skip: int = 0,
        limit: int = 50,
        estado: Optional[str] = None,
        fecha: Optional[date] = None,
        id_paciente: Optional[int] = None
    ) -> tuple[list[Cita], int]:
        """
        Get paginated appointments with filtering.
        Returns: (list of appointments, total count)
        """
        query = self.db.query(Cita)
        
        # Filter by status if provided
        if estado:
            query = query.filter(Cita.estado == estado)
        
        # Filter by date if provided
        if fecha:
            query = query.filter(Cita.fecha == fecha)
        
        # Filter by patient if provided
        if id_paciente:
            query = query.filter(Cita.id_paciente == id_paciente)
        
        # Get total count BEFORE pagination
        total = query.count()
        
        # Apply pagination with ORDER BY for consistent results (most recent first)
        citas = query.order_by(desc(Cita.fecha), Cita.hora).offset(skip).limit(limit).all()
        
        return citas, total

    def get_by_paciente(self, id_paciente: int) -> list[Cita]:
        return self.db.query(Cita).filter(Cita.id_paciente == id_paciente).all()

    def update(self, cita: Cita) -> Cita:
        self.db.commit()
        self.db.refresh(cita)
        return cita

    def delete(self, cita: Cita):
        self.db.delete(cita)
        self.db.commit()
