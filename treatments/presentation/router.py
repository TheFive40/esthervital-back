from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from shared.database import get_db
from treatments.application import use_cases
from treatments.presentation.schemas import (
    TratamientoCreate, TratamientoUpdate, TratamientoResponse, TratamientoDetallado,
    SesionCreate, SesionUpdate, SesionResponse,
    ImagenCreate, ImagenUpdate, ImagenResponse
)
from typing import List

router = APIRouter(
    prefix="/tratamientos",
    tags=["Tratamientos"]
)

@router.post("/", response_model=TratamientoResponse)
def crear_tratamiento(data: TratamientoCreate, db: Session = Depends(get_db)):
    return use_cases.crear_tratamiento(db, data)


@router.get("/", response_model=List[TratamientoResponse])
def listar_tratamientos(db: Session = Depends(get_db)):
    return use_cases.listar_tratamientos(db)


@router.get("/{id_tratamiento}", response_model=TratamientoDetallado)
def obtener_tratamiento_detallado(id_tratamiento: int, db: Session = Depends(get_db)):
    tratamiento = use_cases.obtener_tratamiento_detallado(db, id_tratamiento)
    if not tratamiento:
        raise HTTPException(status_code=404, detail="Tratamiento no encontrado")
    return tratamiento


@router.get("/paciente/{id_paciente}", response_model=List[TratamientoResponse])
def listar_tratamientos_paciente(id_paciente: int, db: Session = Depends(get_db)):
    return use_cases.obtener_tratamientos_por_paciente(db, id_paciente)


@router.put("/{id_tratamiento}", response_model=TratamientoResponse)
def actualizar_tratamiento(
    id_tratamiento: int,
    data: TratamientoUpdate,
    db: Session = Depends(get_db)
):
    tratamiento = use_cases.actualizar_tratamiento(db, id_tratamiento, data)
    if not tratamiento:
        raise HTTPException(status_code=404, detail="Tratamiento no encontrado")
    return tratamiento


@router.delete("/{id_tratamiento}")
def eliminar_tratamiento(id_tratamiento: int, db: Session = Depends(get_db)):
    if not use_cases.eliminar_tratamiento(db, id_tratamiento):
        raise HTTPException(status_code=404, detail="Tratamiento no encontrado")
    return {"message": "Tratamiento eliminado correctamente"}


@router.post("/sesiones", response_model=SesionResponse)
def crear_sesion(data: SesionCreate, db: Session = Depends(get_db)):
    return use_cases.crear_sesion(db, data)


@router.get("/sesiones/tratamiento/{id_tratamiento}", response_model=List[SesionResponse])
def listar_sesiones(id_tratamiento: int, db: Session = Depends(get_db)):
    return use_cases.listar_sesiones_tratamiento(db, id_tratamiento)


@router.get("/sesiones/{id_sesion}", response_model=SesionResponse)
def obtener_sesion(id_sesion: int, db: Session = Depends(get_db)):
    sesion = use_cases.obtener_sesion(db, id_sesion)
    if not sesion:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    return sesion


@router.put("/sesiones/{id_sesion}", response_model=SesionResponse)
def actualizar_sesion(
    id_sesion: int,
    data: SesionUpdate,
    db: Session = Depends(get_db)
):
    sesion = use_cases.actualizar_sesion(db, id_sesion, data)
    if not sesion:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    return sesion


@router.delete("/sesiones/{id_sesion}")
def eliminar_sesion(id_sesion: int, db: Session = Depends(get_db)):
    if not use_cases.eliminar_sesion(db, id_sesion):
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    return {"message": "Sesión eliminada correctamente"}


# ============ IMÁGENES ============
@router.post("/imagenes", response_model=ImagenResponse)
def crear_imagen(data: ImagenCreate, db: Session = Depends(get_db)):
    return use_cases.crear_imagen(db, data)


@router.get("/imagenes/sesion/{id_sesion}", response_model=List[ImagenResponse])
def listar_imagenes_sesion(id_sesion: int, db: Session = Depends(get_db)):
    return use_cases.listar_imagenes_sesion(db, id_sesion)


@router.get("/imagenes/{id_imagen}", response_model=ImagenResponse)
def obtener_imagen(id_imagen: int, db: Session = Depends(get_db)):
    imagen = use_cases.obtener_imagen(db, id_imagen)
    if not imagen:
        raise HTTPException(status_code=404, detail="Imagen no encontrada")
    return imagen


@router.put("/imagenes/{id_imagen}", response_model=ImagenResponse)
def actualizar_imagen(
    id_imagen: int,
    data: ImagenUpdate,
    db: Session = Depends(get_db)
):
    imagen = use_cases.actualizar_imagen(db, id_imagen, data)
    if not imagen:
        raise HTTPException(status_code=404, detail="Imagen no encontrada")
    return imagen


@router.delete("/imagenes/{id_imagen}")
def eliminar_imagen(id_imagen: int, db: Session = Depends(get_db)):
    if not use_cases.eliminar_imagen(db, id_imagen):
        raise HTTPException(status_code=404, detail="Imagen no encontrada")
    return {"message": "Imagen eliminada correctamente"}