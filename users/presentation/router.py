from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from starlette import status
from shared.database import SessionLocal
from users.application import update_usuario
from users.application.change_password import ChangePasswordUseCase
from users.application.delete_usuario import DeleteUsuarioUseCase
from users.presentation.schemas import (
    UsuarioCreate, UsuarioResponse, UsuarioUpdate, CambiarPassword
)
from users.infrastructure.repositories import UsuarioRepository
from users.application.use_cases import CrearUsuarioUseCase

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/", response_model=UsuarioResponse)
def crear_usuario(
    data: UsuarioCreate,
    db: Session = Depends(get_db)
):
    repo = UsuarioRepository(db)
    use_case = CrearUsuarioUseCase(repo)
    return use_case.execute(data)


@router.put("/{id_usuario}")
def actualizar_usuario(id_usuario: int, data: UsuarioUpdate, db: Session = Depends(get_db)):
    use_case = update_usuario.UpdateUsuarioUseCase(UsuarioRepository(db))
    return use_case.execute(db, id_usuario, data)

@router.delete(
    "/{id_usuario}",
    status_code=status.HTTP_204_NO_CONTENT
)
def eliminar_usuario(
    id_usuario: int,
    db: Session = Depends(get_db)
):
    repo = UsuarioRepository(db)
    use_case = DeleteUsuarioUseCase(repo)
    use_case.execute(db, id_usuario)

@router.patch(
    "/{id_usuario}/password"
)
def cambiar_password(
    id_usuario: int,
    data: CambiarPassword,
    db: Session = Depends(get_db)
):
    repo = UsuarioRepository(db)
    use_case = ChangePasswordUseCase(repo)
    return use_case.execute(db, id_usuario, data)
