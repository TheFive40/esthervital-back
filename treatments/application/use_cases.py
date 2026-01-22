from sqlalchemy.orm import Session
from treatments.infrastructure.models import Tratamiento
from treatments.infrastructure.repository import TratamientoRepository
from treatments.presentation.schemas import TratamientoCreate, TratamientoUpdate

repo = TratamientoRepository()

def crear_tratamiento(db: Session, data: TratamientoCreate):
    tratamiento = Tratamiento(**data.dict())
    return repo.create(db, tratamiento)

def listar_tratamientos(db: Session):
    return repo.get_all(db)

def obtener_tratamiento(db: Session, id_tratamiento: int):
    return repo.get_by_id(db, id_tratamiento)

def obtener_tratamientos_por_paciente(db: Session, id_paciente: int):
    return repo.get_by_paciente(db, id_paciente)

def actualizar_tratamiento(db: Session, id_tratamiento: int, data: TratamientoUpdate):
    tratamiento = repo.get_by_id(db, id_tratamiento)
    if not tratamiento:
        return None

    for key, value in data.dict(exclude_unset=True).items():
        setattr(tratamiento, key, value)

    return repo.update(db, tratamiento)

def eliminar_tratamiento(db: Session, id_tratamiento: int):
    tratamiento = repo.get_by_id(db, id_tratamiento)
    if not tratamiento:
        return None
    repo.delete(db, tratamiento)
    return True
