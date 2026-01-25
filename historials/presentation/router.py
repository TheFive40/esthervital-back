from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from shared.database import get_db
from historials.application.use_cases import HistorialService
from historials.presentation.schemas import (
    HistorialCreate, HistorialRead, HistorialUpdate,
    DocumentoCreate, DocumentoRead
)
from typing import List

router = APIRouter(prefix="/historiales", tags=["Historiales Clínicos"])

# --- Historiales ---
@router.post("/", response_model=HistorialRead)
def crear_historial(historial: HistorialCreate, db: Session = Depends(get_db)):
    service = HistorialService(db)
    nuevo = service.crear_historial(historial.dict())
    return nuevo

@router.get("/", response_model=List[HistorialRead])
def listar_todos(db: Session = Depends(get_db)):
    service = HistorialService(db)
    return service.listar_todos()

@router.get("/paciente/{id_paciente}", response_model=List[HistorialRead])
def listar_historiales_paciente(id_paciente: int, db: Session = Depends(get_db)):
    service = HistorialService(db)
    return service.listar_historiales_paciente(id_paciente)

@router.get("/{id_historial}", response_model=HistorialRead)
def obtener_historial(id_historial: int, db: Session = Depends(get_db)):
    service = HistorialService(db)
    historial = service.obtener_historial(id_historial)
    if not historial:
        raise HTTPException(status_code=404, detail="Historial no encontrado")
    return historial

@router.put("/{id_historial}", response_model=HistorialRead)
def actualizar_historial(id_historial: int, data: HistorialUpdate, db: Session = Depends(get_db)):
    service = HistorialService(db)
    historial = service.actualizar_historial(id_historial, data.dict(exclude_unset=True))
    if not historial:
        raise HTTPException(status_code=404, detail="Historial no encontrado")
    return historial

@router.delete("/{id_historial}", response_model=dict)
def eliminar_historial(id_historial: int, db: Session = Depends(get_db)):
    service = HistorialService(db)
    eliminado = service.eliminar_historial(id_historial)
    if not eliminado:
        raise HTTPException(status_code=404, detail="Historial no encontrado")
    return {"message": "Historial eliminado"}

@router.post("/documentos/", response_model=DocumentoRead)
def agregar_documento(documento: DocumentoCreate, db: Session = Depends(get_db)):
    service = HistorialService(db)
    nuevo = service.agregar_documento(documento.dict())
    return nuevo

@router.get("/documentos/{id_historial}", response_model=List[DocumentoRead])
def listar_documentos_historial(id_historial: int, db: Session = Depends(get_db)):
    service = HistorialService(db)
    return service.listar_documentos_historial(id_historial)
