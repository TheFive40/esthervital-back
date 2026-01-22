from sqlalchemy.orm import Session
from appointments.infrastructure.models import Cita
from appointments.infrastructure.repository import CitaRepository

class CitaService:
    def __init__(self, db: Session):
        self.repo = CitaRepository(db)

    def crear_cita(self, data: dict) -> Cita:
        cita = Cita(**data)
        return self.repo.create(cita)

    def obtener_cita(self, id_cita: int) -> Cita | None:
        return self.repo.get_by_id(id_cita)

    def listar_citas(self) -> list[Cita]:
        return self.repo.get_all()

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
