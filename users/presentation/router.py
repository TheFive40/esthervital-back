from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from starlette import status
from typing import List, Optional

from shared.database import get_db
from shared.dependencies import (
    get_current_user,
    get_current_admin,
    get_current_employee,
    require_permission,
    require_write_rate_limit
)
from shared.security_utils import AuditLogger

# Use Cases
from users.application import update_usuario
from users.application.change_password import ChangePasswordUseCase
from users.application.delete_usuario import DeleteUsuarioUseCase
from users.application.use_cases import CrearUsuarioUseCase
from shared.supabase_client import SupabaseAdminError

# Schemas
from users.presentation.schemas import (
    UsuarioCreate, UsuarioResponse, UsuarioUpdate, CambiarPassword, CambiarPasswordPrimerLogin,
    RolCreate, RolResponse, PermisoCreate, PermisoResponse
)

# Repositories
from users.infrastructure.repositories import UsuarioRepository, RolRepository, PermisoRepository

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])


# ============ USUARIOS ENDPOINTS ============

@router.get("/me", response_model=UsuarioResponse)
async def get_me(
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Obtener perfil del usuario autenticado actualmente
    Requiere autenticación
    """
    repo = UsuarioRepository(db)
    usuario = repo.get_by_id(db, current_user["user_id"])

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )

    return usuario


@router.get("/", response_model=List[UsuarioResponse])
async def obtener_usuarios(
        id: Optional[int] = None,
        email: Optional[str] = None,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_admin),  # Solo admin
        request: Request = None
):
    """
    Listar usuarios (solo administrador)
    Filtrable por ID o email
    """
    repo = UsuarioRepository(db)
    client_ip = request.client.host if request.client else current_user.get("ip_address")

    # Log access
    AuditLogger.log_action(
        user_id=current_user["user_id"],
        action="list_usuarios",
        resource="usuario",
        status="success",
        ip_address=client_ip
    )

    if id:
        usuario = repo.get_by_id(db, id)
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        return [usuario]

    if email:
        usuario = repo.get_by_email(email)
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        return [usuario]

    return repo.get_all()


@router.post("/", response_model=UsuarioResponse, dependencies=[Depends(require_write_rate_limit())])
async def crear_usuario(
        data: UsuarioCreate,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_admin),  # Solo admin
        request: Request = None
):
    """
    Crear nuevo usuario (solo administrador)
    Requiere autenticación y permisos de admin
    """
    client_ip = request.client.host if request.client else current_user.get("ip_address")

    repo = UsuarioRepository(db)
    use_case = CrearUsuarioUseCase(repo)

    try:
        nuevo_usuario = use_case.execute(data)

        # Log successful creation
        AuditLogger.log_action(
            user_id=current_user["user_id"],
            action="create_usuario",
            resource="usuario",
            resource_id=nuevo_usuario.id_usuario,
            status="success",
            details={"email": data.email},
            ip_address=client_ip
        )

        return nuevo_usuario

    except SupabaseAdminError as e:
        msg = str(e)
        low = msg.lower()

        # Log failed creation
        AuditLogger.log_action(
            user_id=current_user["user_id"],
            action="create_usuario",
            resource="usuario",
            status="failed",
            details={"error": msg, "email": data.email},
            ip_address=client_ip
        )

        if "already" in low or "duplicate" in low or "exists" in low:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El email ya está en uso"
            )

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Error en el proveedor de autenticación"
        )

    except IntegrityError as e:
        # Log error
        AuditLogger.log_action(
            user_id=current_user["user_id"],
            action="create_usuario",
            resource="usuario",
            status="failed",
            details={"error": "integrity_error", "email": data.email},
            ip_address=client_ip
        )

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El email ya está registrado"
        )

    except Exception as e:
        AuditLogger.log_action(
            user_id=current_user["user_id"],
            action="create_usuario",
            resource="usuario",
            status="failed",
            details={"error": str(e)},
            ip_address=client_ip
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/{id_usuario}", response_model=UsuarioResponse, dependencies=[Depends(require_write_rate_limit())])
async def actualizar_usuario(
        id_usuario: int,
        data: UsuarioUpdate,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user),
        request: Request = None
):
    """
    Actualizar usuario
    Los usuarios normales solo pueden actualizar su propio perfil
    Los admins pueden actualizar cualquier usuario
    """
    client_ip = request.client.host if request.client else current_user.get("ip_address")

    # Check permissions
    if current_user["user_id"] != id_usuario and current_user["id_rol"] != 1:
        AuditLogger.log_action(
            user_id=current_user["user_id"],
            action="update_usuario",
            resource="usuario",
            resource_id=id_usuario,
            status="failed",
            details={"reason": "insufficient_permissions"},
            ip_address=client_ip
        )

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo puedes actualizar tu propio perfil"
        )

    use_case = update_usuario.UpdateUsuarioUseCase(UsuarioRepository(db))
    updated = use_case.execute(db, id_usuario, data)

    AuditLogger.log_action(
        user_id=current_user["user_id"],
        action="update_usuario",
        resource="usuario",
        resource_id=id_usuario,
        status="success",
        ip_address=client_ip
    )

    return updated


@router.delete("/{id_usuario}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require_write_rate_limit())])
async def eliminar_usuario(
        id_usuario: int,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_admin),  # Solo admin
        request: Request = None
):
    """
    Eliminar usuario (solo administrador)
    """
    client_ip = request.client.host if request.client else current_user.get("ip_address")

    repo = UsuarioRepository(db)
    use_case = DeleteUsuarioUseCase(repo)

    try:
        use_case.execute(db, id_usuario)

        AuditLogger.log_action(
            user_id=current_user["user_id"],
            action="delete_usuario",
            resource="usuario",
            resource_id=id_usuario,
            status="success",
            ip_address=client_ip
        )

    except HTTPException:
        AuditLogger.log_action(
            user_id=current_user["user_id"],
            action="delete_usuario",
            resource="usuario",
            resource_id=id_usuario,
            status="failed",
            ip_address=client_ip
        )
        raise


@router.patch("/{id_usuario}/password", dependencies=[Depends(require_write_rate_limit())])
async def cambiar_password(
        id_usuario: int,
        data: CambiarPassword,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user),
        request: Request = None
):
    """
    Cambiar contraseña
    Requiere contraseña actual para verificación
    """
    client_ip = request.client.host if request.client else current_user.get("ip_address")

    # Check permissions
    if current_user["user_id"] != id_usuario and current_user["id_rol"] != 1:
        AuditLogger.log_action(
            user_id=current_user["user_id"],
            action="change_password",
            resource="usuario",
            resource_id=id_usuario,
            status="failed",
            details={"reason": "insufficient_permissions"},
            ip_address=client_ip
        )

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo puedes cambiar tu propia contraseña"
        )

    repo = UsuarioRepository(db)
    use_case = ChangePasswordUseCase(repo)
    result = use_case.execute(db, id_usuario, data)

    AuditLogger.log_action(
        user_id=current_user["user_id"],
        action="change_password",
        resource="usuario",
        resource_id=id_usuario,
        status="success",
        ip_address=client_ip
    )

    return result


@router.patch("/me/primer-login", dependencies=[Depends(require_write_rate_limit())])
async def cambiar_password_primer_login(
        data: CambiarPasswordPrimerLogin,
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db),
        request: Request = None
):
    """
    Cambiar contraseña en primer login
    No requiere contraseña actual
    """
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    client_ip = request.client.host if request.client else current_user.get("ip_address")
    repo = UsuarioRepository(db)
    usuario = repo.get_by_id(db, current_user["user_id"])

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )

    if not usuario.primer_login:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario ya cambió su contraseña inicial"
        )

    # Actualizar contraseña en Supabase Auth si el usuario tiene auth_id
    if usuario.auth_id:
        from shared.supabase_client import SupabaseClient
        supabase = SupabaseClient()
        if supabase.url and supabase.service_role:
            try:
                supabase.update_user_password(usuario.auth_id, data.password_nueva)
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Error updating Supabase password: {e}")
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Error actualizando contraseña en el proveedor de autenticación"
                )

    usuario.password = pwd_context.hash(data.password_nueva)
    usuario.primer_login = False
    repo.update(db, usuario)

    AuditLogger.log_action(
        user_id=current_user["user_id"],
        action="first_login_password_change",
        resource="usuario",
        status="success",
        ip_address=client_ip
    )

    return {"message": "Contraseña establecida correctamente"}


# ============ ROLES ENDPOINTS ============

@router.get("/roles", response_model=List[RolResponse])
async def listar_roles(
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user)
):
    """
    Listar todos los roles disponibles
    """
    repo = RolRepository(db)
    return repo.get_all()


@router.post("/roles", response_model=RolResponse, dependencies=[Depends(require_write_rate_limit())])
async def crear_rol(
        rol: RolCreate,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_admin)  # Solo admin
):
    """
    Crear nuevo rol (solo administrador)
    """
    repo = RolRepository(db)
    return repo.create(rol)


@router.delete("/roles/{id_rol}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require_write_rate_limit())])
async def eliminar_rol(
        id_rol: int,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_admin)  # Solo admin
):
    """
    Eliminar rol (solo administrador)
    """
    repo = RolRepository(db)
    if not repo.delete(id_rol):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rol no encontrado"
        )


# ============ PERMISOS ENDPOINTS ============

@router.get("/permisos", response_model=List[PermisoResponse])
async def listar_permisos(
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user)
):
    """
    Listar todos los permisos disponibles
    """
    repo = PermisoRepository(db)
    return repo.get_all()


@router.post("/permisos", response_model=PermisoResponse, dependencies=[Depends(require_write_rate_limit())])
async def crear_permiso(
        permiso: PermisoCreate,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_admin)  # Solo admin
):
    """
    Crear nuevo permiso (solo administrador)
    """
    repo = PermisoRepository(db)
    return repo.create(permiso)


@router.delete("/permisos/{id_permiso}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require_write_rate_limit())])
async def eliminar_permiso(
        id_permiso: int,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_admin)  # Solo admin
):
    """
    Eliminar permiso (solo administrador)
    """
    repo = PermisoRepository(db)
    if not repo.delete(id_permiso):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permiso no encontrado"
        )