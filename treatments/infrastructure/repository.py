from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, desc, func
from treatments.infrastructure.models import Tratamiento, SesionTratamiento, ImagenSesion
from treatments.infrastructure.payment_models import CostoTratamiento, AbonoTratamiento
from typing import Optional


class TratamientoRepository:

    def _base_query(self, db: Session):
        """Query base con todas las relaciones necesarias cargadas de una vez."""
        return (
            db.query(Tratamiento)
            .options(joinedload(Tratamiento.paciente))
            .options(joinedload(Tratamiento.usuario))
            .options(joinedload(Tratamiento.sesiones).joinedload(SesionTratamiento.imagenes))
            # Cargar costo y sus abonos para calcular resumen financiero sin queries extra
            .options(
                joinedload(Tratamiento.costo).joinedload(CostoTratamiento.abonos)
            )
        )

    def create(self, db: Session, tratamiento: Tratamiento):
        db.add(tratamiento)
        db.commit()
        db.refresh(tratamiento)
        return tratamiento

    def get_all(self, db: Session):
        """Returns all treatments - use get_paginated for large datasets"""
        return self._base_query(db).all()

    def get_paginated(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 50,
        estado: Optional[str] = None,
        id_paciente: Optional[int] = None,
        search: Optional[str] = None,
    ) -> tuple[list, int]:
        query = self._base_query(db)

        if estado:
            query = query.filter(Tratamiento.estado == estado)

        if id_paciente:
            query = query.filter(Tratamiento.id_paciente == id_paciente)

        if search:
            search_term = f"%{search}%"
            query = query.filter(Tratamiento.nombre_tratamiento.ilike(search_term))

        total = query.count()
        treatments = (
            query.order_by(desc(Tratamiento.fecha_inicio))
            .offset(skip)
            .limit(limit)
            .all()
        )

        return treatments, total

    def get_by_id(self, db: Session, id_tratamiento: int):
        return (
            self._base_query(db)
            .filter(Tratamiento.id_tratamiento == id_tratamiento)
            .first()
        )

    def get_by_paciente(self, db: Session, id_paciente: int):
        return (
            db.query(Tratamiento)
            .options(joinedload(Tratamiento.usuario))
            .options(joinedload(Tratamiento.sesiones))
            .options(
                joinedload(Tratamiento.costo).joinedload(CostoTratamiento.abonos)
            )
            .filter(Tratamiento.id_paciente == id_paciente)
            .all()
        )

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
        return (
            db.query(SesionTratamiento)
            .options(joinedload(SesionTratamiento.imagenes))
            .filter(SesionTratamiento.id_sesion == id_sesion)
            .first()
        )

    def get_by_tratamiento(self, db: Session, id_tratamiento: int):
        return (
            db.query(SesionTratamiento)
            .options(joinedload(SesionTratamiento.imagenes))
            .filter(SesionTratamiento.id_tratamiento == id_tratamiento)
            .order_by(SesionTratamiento.numero_sesion)
            .all()
        )

    def update(self, db: Session, sesion: SesionTratamiento):
        db.commit()
        db.refresh(sesion)
        return sesion

    def delete(self, db: Session, sesion: SesionTratamiento):
        db.delete(sesion)
        db.commit()

    def count_by_tratamiento(self, db: Session, id_tratamiento: int) -> int:
        return (
            db.query(SesionTratamiento)
            .filter_by(id_tratamiento=id_tratamiento, estado="Completada")
            .count()
        )

    def count_by_tratamientos_batch(
        self, db: Session, tratamiento_ids: list[int]
    ) -> dict[int, int]:
        """Batch count completed sessions for multiple treatments in a single query."""
        if not tratamiento_ids:
            return {}
        rows = (
            db.query(
                SesionTratamiento.id_tratamiento,
                func.count(SesionTratamiento.id_sesion),
            )
            .filter(
                SesionTratamiento.id_tratamiento.in_(tratamiento_ids),
                SesionTratamiento.estado == "Completada",
            )
            .group_by(SesionTratamiento.id_tratamiento)
            .all()
        )
        return {tid: cnt for tid, cnt in rows}


class ImagenRepository:

    def create(self, db: Session, imagen: ImagenSesion):
        db.add(imagen)
        db.commit()
        db.refresh(imagen)
        return imagen

    def get_by_id(self, db: Session, id_imagen: int):
        return db.query(ImagenSesion).filter_by(id_imagen=id_imagen).first()

    def get_by_sesion(self, db: Session, id_sesion: int):
        return (
            db.query(ImagenSesion)
            .filter_by(id_sesion=id_sesion)
            .order_by(ImagenSesion.fecha_subida)
            .all()
        )

    def update(self, db: Session, imagen: ImagenSesion):
        db.commit()
        db.refresh(imagen)
        return imagen

    def delete(self, db: Session, imagen: ImagenSesion):
        db.delete(imagen)
        db.commit()