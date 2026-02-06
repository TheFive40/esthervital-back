from sqlalchemy.orm import Session
from patients.infrastructure.models import Paciente
from patients.infrastructure.repositories import PacienteRepository
from typing import Optional

class PacienteService:
    def __init__(self, db: Session):
        self.repo = PacienteRepository(db)

    def crear_paciente(self, data: dict) -> Paciente:
        paciente = Paciente(**data)
        return self.repo.create(paciente)

    def listar_pacientes(self) -> list[Paciente]:
        """Returns all patients - use listar_pacientes_paginados for large datasets"""
        return self.repo.get_all()

    def listar_pacientes_paginados(
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
        return self.repo.get_paginated(skip, limit, estado, search)

    def obtener_paciente(self, id_paciente: int) -> Paciente | None:
        return self.repo.get_by_id(id_paciente)

    def actualizar_paciente(self, id_paciente: int, data: dict) -> Paciente | None:
        paciente = self.repo.get_by_id(id_paciente)
        if not paciente:
            return None
        for key, value in data.items():
            setattr(paciente, key, value)
        return self.repo.update(paciente)

    def eliminar_paciente(self, id_paciente: int) -> bool:
        paciente = self.repo.get_by_id(id_paciente)
        if not paciente:
            return False
        self.repo.soft_delete(paciente)
        return True

    def buscar_por_cc(self, numero_identificacion: str) -> Paciente | None:
        return self.repo.get_by_identificacion(numero_identificacion)
