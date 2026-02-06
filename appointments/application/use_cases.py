from sqlalchemy.orm import Session
from appointments.infrastructure.models import Cita
from appointments.infrastructure.repository import CitaRepository
from typing import Optional
from datetime import date

class CitaService:
    def __init__(self, db: Session):
        self.repo = CitaRepository(db)

    def crear_cita(self, data: dict) -> Cita:
        cita = Cita(**data)
        return self.repo.create(cita)

    def obtener_cita(self, id_cita: int) -> Cita | None:
        return self.repo.get_by_id(id_cita)

    def listar_citas(self) -> list[Cita]:
        """Returns all appointments - use listar_citas_paginadas for large datasets"""
        return self.repo.get_all()

    def listar_citas_paginadas(
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
        return self.repo.get_paginated(skip, limit, estado, fecha, id_paciente)

    def listar_citas_paciente(self, id_paciente: int) -> list[Cita]:
        return self.repo.get_by_paciente(id_paciente)

    def actualizar_cita(self, id_cita: int, data: dict) -> Cita | None:
        cita = self.repo.get_by_id(id_cita)
        if not cita:
            return None
        for key, value in data.items():
            setattr(cita, key, value)
        return self.repo.update(cita)

    def eliminar_cita(self, id_cita: int) -> bool:
        cita = self.repo.get_by_id(id_cita)
        if not cita:
            return False
        self.repo.delete(cita)
        return True
