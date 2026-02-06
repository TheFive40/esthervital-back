"""
Enhanced FastAPI dependencies for authentication and authorization
"""

from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import Optional, List

from shared.database import get_db
from shared.rate_limiter import AUTH_LIMITER, USER_LIMITER, WRITE_LIMITER
from shared.security_utils import TokenManager, PermissionChecker, AuditLogger
from users.infrastructure.repositories import UsuarioRepository


async def get_current_user(
        request: Request,
        db: Session = Depends(get_db)
) -> dict:
    """
    Get current authenticated user from JWT token
    Validates token and checks rate limits
    Supports both local JWT tokens and Supabase tokens
    """
    # Extract token from Authorization header
    auth_header = request.headers.get("Authorization")

    if not auth_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
            headers={"WWW-Authenticate": "Bearer"}
        )

    try:
        scheme, token = auth_header.split()
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme",
                headers={"WWW-Authenticate": "Bearer"}
            )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Verify token (supports both local and Supabase tokens)
    payload = TokenManager.verify_token(token)
    
    repo = UsuarioRepository(db)
    usuario = None
    user_id = None
    
    # Check if token is from Supabase (has "supabase_user" key) or local
    if payload.get("type") == "supabase":
        # Supabase token - find user by email
        email = payload.get("email")
        if email:
            usuario = repo.get_by_email(email.lower())
            if usuario:
                user_id = usuario.id_usuario
    else:
        # Local token - find user by ID
        user_id = int(payload.get("sub"))
        usuario = repo.get_by_id(db, user_id)

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found in database"
        )
    
    user_id = usuario.id_usuario

    # Check user rate limit
    allowed, info = USER_LIMITER.is_allowed(f"user:{user_id}")
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={
                "X-RateLimit-Limit": str(info["limit"]),
                "X-RateLimit-Remaining": str(info["remaining"]),
                "X-RateLimit-Reset": info["reset_at"],
                "Retry-After": str(info["window_seconds"])
            }
        )

    if usuario.estado != "Activo":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    # Log successful authentication
    client_ip = request.client.host if request.client else "unknown"
    AuditLogger.log_action(
        user_id=user_id,
        action="request_authenticated",
        resource="auth",
        status="success",
        ip_address=client_ip
    )

    return {
        "user_id": user_id,
        "email": usuario.email,
        "nombre": usuario.nombre,
        "apellido": usuario.apellido,
        "id_rol": usuario.id_rol,
        "estado": usuario.estado,
        "primer_login": usuario.primer_login,
        "ip_address": client_ip
    }


async def get_current_admin(
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db)
) -> dict:
    """
    Dependency that ensures user is an administrator
    """
    if not PermissionChecker.is_admin(current_user["user_id"], db):
        # Log unauthorized access attempt
        AuditLogger.log_action(
            user_id=current_user["user_id"],
            action="unauthorized_access_attempt",
            resource="admin",
            status="failed",
            ip_address=current_user.get("ip_address")
        )

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
            headers={"X-Error": "insufficient_permissions"}
        )

    return current_user


async def get_current_employee(
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db)
) -> dict:
    """
    Dependency that ensures user is an employee or admin
    """
    if not PermissionChecker.is_employee(current_user["user_id"], db) and \
            not PermissionChecker.is_admin(current_user["user_id"], db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Employee or higher access required"
        )

    return current_user


def require_permission(permission: str):
    """
    Dependency factory to check for specific permission
    Usage: @router.get("/endpoint", dependencies=[Depends(require_permission("read_patient"))])
    """

    async def check_permission(
            current_user: dict = Depends(get_current_user),
            db: Session = Depends(get_db)
    ) -> dict:
        if not PermissionChecker.has_permission(current_user["user_id"], permission, db):
            # Log unauthorized access attempt
            AuditLogger.log_action(
                user_id=current_user["user_id"],
                action="unauthorized_access_attempt",
                resource=permission,
                status="failed",
                ip_address=current_user.get("ip_address")
            )

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission required: {permission}",
                headers={"X-Required-Permission": permission}
            )

        return current_user

    return check_permission


def require_any_permission(permissions: List[str]):
    """
    Dependency factory to check for any of the permissions
    """

    async def check_permissions(
            current_user: dict = Depends(get_current_user),
            db: Session = Depends(get_db)
    ) -> dict:
        if not PermissionChecker.has_any_permission(current_user["user_id"], permissions, db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"One of these permissions required: {', '.join(permissions)}"
            )

        return current_user

    return check_permissions


def require_all_permissions(permissions: List[str]):
    """
    Dependency factory to check for all permissions
    """

    async def check_permissions(
            current_user: dict = Depends(get_current_user),
            db: Session = Depends(get_db)
    ) -> dict:
        if not PermissionChecker.has_all_permissions(current_user["user_id"], permissions, db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"All these permissions required: {', '.join(permissions)}"
            )

        return current_user

    return check_permissions


def require_write_rate_limit():
    """
    Dependency to enforce stricter rate limits for write operations
    Usage: @router.post("/endpoint", dependencies=[Depends(require_write_rate_limit())])
    """

    async def check_write_limit(current_user: dict = Depends(get_current_user)) -> dict:
        user_id = current_user["user_id"]
        allowed, info = WRITE_LIMITER.is_allowed(f"write:{user_id}")

        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Write rate limit exceeded",
                headers={
                    "X-RateLimit-Limit": str(info["limit"]),
                    "X-RateLimit-Remaining": str(info["remaining"]),
                    "X-RateLimit-Reset": info["reset_at"],
                    "Retry-After": str(info["window_seconds"])
                }
            )

        return current_user

    return check_write_limit


async def verify_resource_ownership(
        user_id: int,
        resource_owner_id: int,
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db)
) -> bool:
    """
    Verify that the current user owns the resource or is an admin
    """
    if current_user["user_id"] != resource_owner_id:
        if not PermissionChecker.is_admin(current_user["user_id"], db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this resource"
            )

    return True


async def verify_patient_access(
        patient_id: int,
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db)
) -> dict:
    """
    Verify that user has permission to access patient data
    """
    from patients.infrastructure.repositories import PacienteRepository

    repo = PacienteRepository(db)
    patient = repo.get_by_id(patient_id)

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )

    # Log access
    AuditLogger.log_action(
        user_id=current_user["user_id"],
        action="access_patient",
        resource="paciente",
        resource_id=patient_id,
        ip_address=current_user.get("ip_address")
    )

    return patient