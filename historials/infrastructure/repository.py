from sqlalchemy.orm import Session
from historials.infrastructure.models import HistorialClinico, DocumentoClinico

class HistorialRepository:
    def __init__(self, db: Session):
        self.db = db

    # Historiales
    def create_historial(self, historial: HistorialClinico) -> HistorialClinico:
        self.db.add(historial)
        self.db.commit()
        self.db.refresh(historial)
        return historial

    def get_historial(self, id_historial: int) -> HistorialClinico | None:
        return self.db.query(HistorialClinico).filter(HistorialClinico.id_historial==id_historial).first()

    def get_historiales_paciente(self, id_paciente: int) -> list[HistorialClinico]:
        return self.db.query(HistorialClinico).filter(HistorialClinico.id_paciente==id_paciente).all()

    def update_historial(self, historial: HistorialClinico) -> HistorialClinico:
        self.db.commit()
        self.db.refresh(historial)
        return historial

    def delete_historial(self, historial: HistorialClinico):
        self.db.delete(historial)
        self.db.commit()

    def create_documento(self, documento: DocumentoClinico) -> DocumentoClinico:
        self.db.add(documento)
        self.db.commit()
        self.db.refresh(documento)
        return documento

    def get_documentos_historial(self, id_historial: int) -> list[DocumentoClinico]:
        return self.db.query(DocumentoClinico).filter(DocumentoClinico.id_historial==id_historial).all()

    def get_documento(self, id_documento: int) -> DocumentoClinico | None:
        return self.db.query(DocumentoClinico).filter(DocumentoClinico.id_documento==id_documento).first()

    def delete_documento(self, documento: DocumentoClinico):
        self.db.delete(documento)
        self.db.commit()

    def get_all(self) -> list[HistorialClinico]:
        return self.db.query(HistorialClinico).all()

    def get_paginated(self, skip: int = 0, limit: int = 50) -> tuple[list[HistorialClinico], int]:
        """Get paginated historials with total count using SQL OFFSET/LIMIT."""
        query = self.db.query(HistorialClinico)
        total = query.count()
        items = query.order_by(HistorialClinico.id_historial.desc()).offset(skip).limit(limit).all()
        return items, total
