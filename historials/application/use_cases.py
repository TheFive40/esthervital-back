from sqlalchemy.orm import Session
from historials.infrastructure.models import HistorialClinico, DocumentoClinico
from historials.infrastructure.repository import HistorialRepository

class HistorialService:
    def __init__(self, db: Session):
        self.repo = HistorialRepository(db)

    def crear_historial(self, data: dict) -> HistorialClinico:
        historial = HistorialClinico(**data)
        return self.repo.create_historial(historial)

    def obtener_historial(self, id_historial: int) -> HistorialClinico | None:
        return self.repo.get_historial(id_historial)

    def listar_historiales_paciente(self, id_paciente: int) -> list[HistorialClinico]:
        return self.repo.get_historiales_paciente(id_paciente)

    def actualizar_historial(self, id_historial: int, data: dict) -> HistorialClinico | None:
        historial = self.repo.get_historial(id_historial)
        if not historial:
            return None
        for key, value in data.items():
            setattr(historial, key, value)
        return self.repo.update_historial(historial)

    def eliminar_historial(self, id_historial: int) -> bool:
        historial = self.repo.get_historial(id_historial)
        if not historial:
            return False
        self.repo.delete_historial(historial)
        return True

    def agregar_documento(self, data: dict) -> DocumentoClinico:
        documento = DocumentoClinico(**data)
        return self.repo.create_documento(documento)

    def listar_documentos_historial(self, id_historial: int) -> list[DocumentoClinico]:
        return self.repo.get_documentos_historial(id_historial)

    def eliminar_documento(self, id_documento: int) -> bool:
        documento = self.repo.get_documento(id_documento)
        if not documento:
            return False
        self.repo.delete_documento(documento)
        return True

    def listar_todos(self) -> list[HistorialClinico]:
        return self.repo.get_all()

    def listar_todos_paginados(self, skip: int = 0, limit: int = 50) -> tuple[list[HistorialClinico], int]:
        """Get paginated historials. Returns (items, total_count)."""
        return self.repo.get_paginated(skip, limit)
