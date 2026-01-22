from sqlalchemy.orm import Session
from pacientes.infrastructure.models import Paciente
from pacientes.infrastructure.repository import PacienteRepository

class PacienteService:
    def __init__(self, db: Session):
        self.repo = PacienteRepository(db)

    def crear_paciente(self, data: dict) -> Paciente:
        paciente = Paciente(**data)
        return self.repo.create(paciente)

    def listar_pacientes(self) -> list[Paciente]:
        return self.repo.get_all()

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
