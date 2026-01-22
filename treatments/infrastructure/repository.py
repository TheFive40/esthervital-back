from sqlalchemy.orm import Session
from treatments.infrastructure.models import Tratamiento

class TratamientoRepository:

    def create(self, db: Session, tratamiento: Tratamiento):
        db.add(tratamiento)
        db.commit()
        db.refresh(tratamiento)
        return tratamiento

    def get_all(self, db: Session):
        return db.query(Tratamiento).all()

    def get_by_id(self, db: Session, id_tratamiento: int):
        return db.query(Tratamiento).filter_by(id_tratamiento=id_tratamiento).first()

    def get_by_paciente(self, db: Session, id_paciente: int):
        return db.query(Tratamiento).filter_by(id_paciente=id_paciente).all()

    def update(self, db: Session, tratamiento: Tratamiento):
        db.commit()
        db.refresh(tratamiento)
        return tratamiento

    def delete(self, db: Session, tratamiento: Tratamiento):
        db.delete(tratamiento)
        db.commit()
