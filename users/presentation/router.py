from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
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
from shared.supabase_client import SupabaseAdminError

# Schemas (Agregamos los nuevos)
from users.presentation.schemas import (
    UsuarioCreate, UsuarioResponse, UsuarioUpdate, CambiarPassword, CambiarPasswordPrimerLogin,
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
    
    email = email.lower()
    print(f"DEBUG /me: Searching for email '{email}'")

    usuario = repo.get_by_email(email)
    
    # Auto-provisioning mechanism for "Orphan" Auth users
    if not usuario:
        print(f"DEBUG /me: Usuario no encontrado en DB local. Intentando auto-recuperación desde Token...")
        try:
            # Extract basic info from token metadata
            user_metadata = current_user.get("user_metadata", {})
            auth_id = current_user.get("sub")
            
            if not auth_id:
                raise Exception("Token sin 'sub' (auth_id)")

            nombre = user_metadata.get("nombre", "Usuario")
            apellido = user_metadata.get("apellido", "Nuevo")
            
            # Default Role: Check if 'id_rol' is in metadata, otherwise default to 2 (Empleado) or 1?
            # Safer to default to Empleado (2) if not specified to avoid unwanted Admin access.
            id_rol = user_metadata.get("id_rol")
            if not id_rol:
                 id_rol = 2 # Default fallback
            
            from users.infrastructure.models import Usuario
            from passlib.context import CryptContext
            
            # Create local user
            nuevo_usuario = Usuario(
                nombre=nombre,
                apellido=apellido,
                email=email,
                auth_id=auth_id,
                id_rol=int(id_rol),
                estado="Activo",
                password=None # Password handled by Supabase
            )
            
            repo.create(nuevo_usuario)
            print(f"DEBUG /me: Usuario {email} recuperado y creado en BD local exitosamente.")
            return nuevo_usuario
            
        except Exception as e:
            print(f"DEBUG /me: Auto-recuperación falló: {e}")
            raise HTTPException(status_code=404, detail="Usuario no encontrado en base de datos y falló la auto-recuperación")
    
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
    try:
        return use_case.execute(data)
    except SupabaseAdminError as e:
        msg = str(e)
        low = msg.lower()
        if "already" in low or "duplicate" in low or "exists" in low:
            # This might still be raised if recovery failed in UseCase
            raise HTTPException(status_code=409, detail="El email ya está en uso en el proveedor de autenticación y no se pudo vincular")
        # Bad gateway to auth provider
        raise HTTPException(status_code=502, detail=f"Error creando usuario en proveedor de autenticación: {msg}")
    except IntegrityError as e:
        # Local DB duplicate or FK error
        print(f"DEBUG Create User IntegrityError: {e}")
        raise HTTPException(status_code=409, detail="El email ya está registrado en el sistema (o error de integridad)")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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


@router.patch("/me/primer-login")
def cambiar_password_primer_login(
    data: CambiarPasswordPrimerLogin,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cambiar contraseña en primer login (no requiere contraseña actual)"""
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    repo = UsuarioRepository(db)
    email = current_user.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Token inválido")
    
    usuario = repo.get_by_email(email)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    if not usuario.primer_login:
        raise HTTPException(status_code=400, detail="El usuario ya cambió su contraseña inicial")
    
    usuario.password = pwd_context.hash(data.password_nueva)
    usuario.primer_login = False
    repo.update(db, usuario)
    
    return {"message": "Contraseña establecida correctamente"}


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