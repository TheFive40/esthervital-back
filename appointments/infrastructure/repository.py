from sqlalchemy.orm import Session
from appointments.infrastructure.models import Cita

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
        return self.db.query(Cita).all()

    def get_by_paciente(self, id_paciente: int) -> list[Cita]:
        return self.db.query(Cita).filter(Cita.id_paciente == id_paciente).all()

    def update(self, cita: Cita) -> Cita:
        self.db.commit()
        self.db.refresh(cita)
        return cita

    def delete(self, cita: Cita):
        self.db.delete(cita)
        self.db.commit()
