from sqlalchemy.orm import Session
from pacientes.infrastructure.models import Paciente

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
        return self.db.query(Paciente).filter(Paciente.estado=="Activo").all()

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
