from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from shared.database import get_db
from treatments.application import use_cases
from treatments.presentation.schemas import (
    TratamientoCreate,
    TratamientoUpdate,
    TratamientoResponse
)
from typing import List

router = APIRouter(
    prefix="/tratamientos",
    tags=["Tratamientos"]
)

@router.post("/", response_model=TratamientoResponse)
def crear(data: TratamientoCreate, db: Session = Depends(get_db)):
    return use_cases.crear_tratamiento(db, data)

@router.get("/", response_model=List[TratamientoResponse])
def listar(db: Session = Depends(get_db)):
    return use_cases.listar_tratamientos(db)

@router.get("/{id_tratamiento}", response_model=TratamientoResponse)
def obtener(id_tratamiento: int, db: Session = Depends(get_db)):
    tratamiento = use_cases.obtener_tratamiento(db, id_tratamiento)
    if not tratamiento:
        raise HTTPException(status_code=404, detail="Tratamiento no encontrado")
    return tratamiento

@router.get("/paciente/{id_paciente}", response_model=List[TratamientoResponse])
def listar_por_paciente(id_paciente: int, db: Session = Depends(get_db)):
    return use_cases.obtener_tratamientos_por_paciente(db, id_paciente)

@router.put("/{id_tratamiento}", response_model=TratamientoResponse)
def actualizar(id_tratamiento: int, data: TratamientoUpdate, db: Session = Depends(get_db)):
    tratamiento = use_cases.actualizar_tratamiento(db, id_tratamiento, data)
    if not tratamiento:
        raise HTTPException(status_code=404, detail="Tratamiento no encontrado")
    return tratamiento

@router.delete("/{id_tratamiento}")
def eliminar(id_tratamiento: int, db: Session = Depends(get_db)):
    if not use_cases.eliminar_tratamiento(db, id_tratamiento):
        raise HTTPException(status_code=404, detail="Tratamiento no encontrado")
    return {"message": "Tratamiento eliminado correctamente"}
