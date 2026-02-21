from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from patients.infrastructure.consent_models import ConsentimientoPaciente
from patients.infrastructure.consent_repository import ConsentimientoRepository
from typing import Optional, List


class ConsentimientoService:
    def __init__(self, db: Session):
        self.repo = ConsentimientoRepository(db)

    def crear_consentimiento(
        self,
        id_paciente: int,
        tipo_consentimiento: str,
        url_archivo: str,
        nombre_archivo: str,
        tipo_archivo: Optional[str] = None,
        observaciones: Optional[str] = None,
        subido_por: Optional[int] = None
    ) -> ConsentimientoPaciente:
        """
        Registra un consentimiento informado para un paciente.
        El archivo ya debe estar subido a Supabase Storage (u otro proveedor)
        y se recibe la URL resultante.
        """
        consentimiento = ConsentimientoPaciente(
            id_paciente=id_paciente,
            tipo_consentimiento=tipo_consentimiento,
            url_archivo=url_archivo,
            nombre_archivo=nombre_archivo,
            tipo_archivo=tipo_archivo,
            observaciones=observaciones,
            subido_por=subido_por,
        )
        return self.repo.create(consentimiento)

    def listar_consentimientos_paciente(
        self,
        id_paciente: int,
        solo_activos: bool = True
    ) -> List[ConsentimientoPaciente]:
        return self.repo.get_by_paciente(id_paciente, solo_activos)

    def obtener_consentimiento(self, id_consentimiento: int) -> ConsentimientoPaciente:
        c = self.repo.get_by_id(id_consentimiento)
        if not c:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Consentimiento no encontrado"
            )
        return c

    def actualizar_observaciones(
        self,
        id_consentimiento: int,
        observaciones: str
    ) -> ConsentimientoPaciente:
        c = self.obtener_consentimiento(id_consentimiento)
        c.observaciones = observaciones
        return self.repo.update(c)

    def eliminar_consentimiento(self, id_consentimiento: int) -> None:
        """Soft delete: el registro permanece en BD pero marcado inactivo."""
        c = self.obtener_consentimiento(id_consentimiento)
        self.repo.soft_delete(c)