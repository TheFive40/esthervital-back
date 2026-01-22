from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from shared.database import get_db
from patients.application.use_cases import PacienteService
from patients.presentation.schemas import PacienteCreate, PacienteUpdate, PacienteRead
from typing import List

router = APIRouter(prefix="/pacientes", tags=["Pacientes"])

@router.post("/", response_model=PacienteRead)
def crear_paciente(paciente: PacienteCreate, db: Session = Depends(get_db)):
    service = PacienteService(db)
    nuevo = service.crear_paciente(paciente.dict())
    return nuevo

@router.get("/", response_model=List[PacienteRead])
def listar_pacientes(db: Session = Depends(get_db)):
    service = PacienteService(db)
    return service.listar_pacientes()

@router.get("/{id_paciente}", response_model=PacienteRead)
def obtener_paciente(id_paciente: int, db: Session = Depends(get_db)):
    service = PacienteService(db)
    paciente = service.obtener_paciente(id_paciente)
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    return paciente

@router.put("/{id_paciente}", response_model=PacienteRead)
def actualizar_paciente(id_paciente: int, data: PacienteUpdate, db: Session = Depends(get_db)):
    service = PacienteService(db)
    paciente = service.actualizar_paciente(id_paciente, data.dict(exclude_unset=True))
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    return paciente

@router.delete("/{id_paciente}", response_model=dict)
def eliminar_paciente(id_paciente: int, db: Session = Depends(get_db)):
    service = PacienteService(db)
    eliminado = service.eliminar_paciente(id_paciente)
    if not eliminado:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    return {"message": "Paciente eliminado (lógico)"}

@router.get("/buscar/{numero_identificacion}", response_model=PacienteRead)
def buscar_paciente(numero_identificacion: str, db: Session = Depends(get_db)):
    service = PacienteService(db)
    paciente = service.buscar_por_cc(numero_identificacion)
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    return paciente
