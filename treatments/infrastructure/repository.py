from sqlalchemy.orm import Session, joinedload
from treatments.infrastructure.models import Tratamiento, SesionTratamiento, ImagenSesion

class TratamientoRepository:

    def create(self, db: Session, tratamiento: Tratamiento):
        db.add(tratamiento)
        db.commit()
        db.refresh(tratamiento)
        return tratamiento

    def get_all(self, db: Session):
        return db.query(Tratamiento)\
            .options(joinedload(Tratamiento.paciente))\
            .options(joinedload(Tratamiento.usuario))\
            .options(joinedload(Tratamiento.sesiones))\
            .all()

    def get_by_id(self, db: Session, id_tratamiento: int):
        return db.query(Tratamiento)\
            .options(joinedload(Tratamiento.paciente))\
            .options(joinedload(Tratamiento.usuario))\
            .options(joinedload(Tratamiento.sesiones).joinedload(SesionTratamiento.imagenes))\
            .filter_by(id_tratamiento=id_tratamiento)\
            .first()

    def get_by_paciente(self, db: Session, id_paciente: int):
        return db.query(Tratamiento)\
            .options(joinedload(Tratamiento.usuario))\
            .options(joinedload(Tratamiento.sesiones))\
            .filter_by(id_paciente=id_paciente)\
            .all()

    def update(self, db: Session, tratamiento: Tratamiento):
        db.commit()
        db.refresh(tratamiento)
        return tratamiento

    def delete(self, db: Session, tratamiento: Tratamiento):
        db.delete(tratamiento)
        db.commit()


class SesionRepository:

    def create(self, db: Session, sesion: SesionTratamiento):
        db.add(sesion)
        db.commit()
        db.refresh(sesion)
        return sesion

    def get_by_id(self, db: Session, id_sesion: int):
        return db.query(SesionTratamiento)\
            .options(joinedload(SesionTratamiento.imagenes))\
            .filter_by(id_sesion=id_sesion)\
            .first()

    def get_by_tratamiento(self, db: Session, id_tratamiento: int):
        return db.query(SesionTratamiento)\
            .options(joinedload(SesionTratamiento.imagenes))\
            .filter_by(id_tratamiento=id_tratamiento)\
            .order_by(SesionTratamiento.numero_sesion)\
            .all()

    def update(self, db: Session, sesion: SesionTratamiento):
        db.commit()
        db.refresh(sesion)
        return sesion

    def delete(self, db: Session, sesion: SesionTratamiento):
        db.delete(sesion)
        db.commit()

    def count_by_tratamiento(self, db: Session, id_tratamiento: int) -> int:
        return db.query(SesionTratamiento)\
            .filter_by(id_tratamiento=id_tratamiento, estado="Completada")\
            .count()


class ImagenRepository:

    def create(self, db: Session, imagen: ImagenSesion):
        db.add(imagen)
        db.commit()
        db.refresh(imagen)
        return imagen

    def get_by_id(self, db: Session, id_imagen: int):
        return db.query(ImagenSesion).filter_by(id_imagen=id_imagen).first()

    def get_by_sesion(self, db: Session, id_sesion: int):
        return db.query(ImagenSesion)\
            .filter_by(id_sesion=id_sesion)\
            .order_by(ImagenSesion.fecha_subida)\
            .all()

    def update(self, db: Session, imagen: ImagenSesion):
        db.commit()
        db.refresh(imagen)
        return imagen

    def delete(self, db: Session, imagen: ImagenSesion):
        db.delete(imagen)
        db.commit()