from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from shared.database import get_db
from appointments.application.use_cases import CitaService
from appointments.presentation.schemas import CitaCreate, CitaUpdate, CitaRead
from typing import List

router = APIRouter(prefix="/citas", tags=["Citas"])

@router.post("/", response_model=CitaRead)
def crear_cita(cita: CitaCreate, db: Session = Depends(get_db)):
    service = CitaService(db)
    nuevo = service.crear_cita(cita.dict())
    return nuevo

@router.get("/", response_model=List[CitaRead])
def listar_citas(db: Session = Depends(get_db)):
    service = CitaService(db)
    return service.listar_citas()

@router.get("/paciente/{id_paciente}", response_model=List[CitaRead])
def listar_citas_paciente(id_paciente: int, db: Session = Depends(get_db)):
    service = CitaService(db)
    return service.listar_citas_paciente(id_paciente)

@router.get("/{id_cita}", response_model=CitaRead)
def obtener_cita(id_cita: int, db: Session = Depends(get_db)):
    service = CitaService(db)
    cita = service.obtener_cita(id_cita)
    if not cita:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    return cita

@router.put("/{id_cita}", response_model=CitaRead)
def actualizar_cita(id_cita: int, data: CitaUpdate, db: Session = Depends(get_db)):
    service = CitaService(db)
    cita = service.actualizar_cita(id_cita, data.dict(exclude_unset=True))
    if not cita:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    return cita

@router.delete("/{id_cita}", response_model=dict)
def eliminar_cita(id_cita: int, db: Session = Depends(get_db)):
    service = CitaService(db)
    eliminado = service.eliminar_cita(id_cita)
    if not eliminado:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    return {"message": "Cita eliminada"}
