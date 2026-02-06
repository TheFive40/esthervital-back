from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from patients.infrastructure.models import Paciente
from typing import Optional

class PacienteRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, paciente: Paciente) -> Paciente:
        self.db.add(paciente)
        self.db.commit()
        self.db.refresh(paciente)
        return paciente

    def get_by_id(self, id_paciente: int) -> Paciente | None:
        return self.db.query(Paciente).filter(Paciente.id_paciente == id_paciente).first()

    def get_all(self) -> list[Paciente]:
        """Returns all patients - use get_paginated for large datasets"""
        return self.db.query(Paciente).all()

    def get_paginated(
        self,
        skip: int = 0,
        limit: int = 50,
        estado: Optional[str] = None,
        search: Optional[str] = None
    ) -> tuple[list[Paciente], int]:
        """
        Get paginated patients with filtering.
        Returns: (list of patients, total count)
        """
        query = self.db.query(Paciente)
        
        # Filter by status if provided
        if estado:
            query = query.filter(Paciente.estado == estado)
        
        # Search by name, apellido, or identificacion
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Paciente.nombre.ilike(search_term),
                    Paciente.apellido.ilike(search_term),
                    Paciente.numero_identificacion.ilike(search_term)
                )
            )
        
        # Get total count BEFORE pagination
        total = query.count()
        
        # Apply pagination with ORDER BY for consistent results
        patients = query.order_by(Paciente.fecha_registro.desc()).offset(skip).limit(limit).all()
        
        return patients, total

    def get_by_identificacion(self, numero_identificacion: str) -> Paciente | None:
        return self.db.query(Paciente).filter(Paciente.numero_identificacion==numero_identificacion).first()

    def update(self, paciente: Paciente) -> Paciente:
        self.db.commit()
        self.db.refresh(paciente)
        return paciente

    def soft_delete(self, paciente: Paciente):
        paciente.estado = "Inactivo"
        self.db.commit()
        self.db.refresh(paciente)
