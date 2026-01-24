from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette import status
from typing import List, Optional

# Importamos get_db desde tu archivo shared (Más limpio)
from shared.database import get_db

# Use Cases existentes
from users.application import update_usuario
from users.application.change_password import ChangePasswordUseCase
from users.application.delete_usuario import DeleteUsuarioUseCase
from users.application.use_cases import CrearUsuarioUseCase

# Schemas (Agregamos los nuevos)
from users.presentation.schemas import (
    UsuarioCreate, UsuarioResponse, UsuarioUpdate, CambiarPassword,
    RolCreate, RolResponse, PermisoCreate, PermisoResponse
)

# Repositorios (Agregamos los nuevos)
from users.infrastructure.repositories import UsuarioRepository, RolRepository, PermisoRepository
from shared.security import get_current_user

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])

@router.get("/me", response_model=UsuarioResponse)
def get_me(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Obtener perfil del usuario autenticado actualmente"""
    # current_user is the decoded JWT payload
    # In a real app we might query the DB by auth_id (sub) to get the full profile
    # For now, let's find by email or auth_id if we have it synced
    repo = UsuarioRepository(db)
    # Assuming the token has email. Supabase tokens have 'email' claim.
    email = current_user.get("email")
    if not email:
         raise HTTPException(status_code=400, detail="Token inválido")
    
    usuario = repo.get_by_email(email)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado en base de datos")
    
    return usuario

# --- ENDPOINT MEJORADO: GET USUARIOS (Todos o Filtro) ---
# Este va ANTES del POST para mantener orden, pero funciona igual donde sea
@router.get("/", response_model=List[UsuarioResponse])
def obtener_usuarios(
    id: Optional[int] = None, 
    email: Optional[str] = None, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user) # Protected
):
    repo = UsuarioRepository(db)
    
    if id:
        usuario = repo.get_by_id(db, id)
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        return [usuario]
        
    if email:
        usuario = repo.get_by_email(email)
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        return [usuario]

    return repo.get_all()


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

@router.delete("/{id_usuario}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_usuario(id_usuario: int, db: Session = Depends(get_db)):
    repo = UsuarioRepository(db)
    use_case = DeleteUsuarioUseCase(repo)
    use_case.execute(db, id_usuario)

@router.patch("/{id_usuario}/password")
def cambiar_password(
    id_usuario: int,
    data: CambiarPassword,
    db: Session = Depends(get_db)
):
    repo = UsuarioRepository(db)
    use_case = ChangePasswordUseCase(repo)
    return use_case.execute(db, id_usuario, data)

# --- NUEVOS ENDPOINTS: ROLES Y PERMISOS ---
# (Quedarán disponibles en /usuarios/roles y /usuarios/permisos)

# ROLES
@router.get("/roles", response_model=List[RolResponse])
def listar_roles(db: Session = Depends(get_db)):
    repo = RolRepository(db)
    return repo.get_all()

@router.post("/roles", response_model=RolResponse)
def crear_rol(rol: RolCreate, db: Session = Depends(get_db)):
    repo = RolRepository(db)
    return repo.create(rol)

@router.delete("/roles/{id_rol}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_rol(id_rol: int, db: Session = Depends(get_db)):
    repo = RolRepository(db)
    if not repo.delete(id_rol):
        raise HTTPException(status_code=404, detail="Rol no encontrado")

# PERMISOS
@router.get("/permisos", response_model=List[PermisoResponse])
def listar_permisos(db: Session = Depends(get_db)):
    repo = PermisoRepository(db)
    return repo.get_all()

@router.post("/permisos", response_model=PermisoResponse)
def crear_permiso(permiso: PermisoCreate, db: Session = Depends(get_db)):
    repo = PermisoRepository(db)
    return repo.create(permiso)

@router.delete("/permisos/{id_permiso}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_permiso(id_permiso: int, db: Session = Depends(get_db)):
    repo = PermisoRepository(db)
    if not repo.delete(id_permiso):
        raise HTTPException(status_code=404, detail="Permiso no encontrado")