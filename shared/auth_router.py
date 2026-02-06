"""
Authentication endpoints for user login and token management
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext

from shared.database import get_db
from shared.rate_limiter import AUTH_LIMITER
from shared.security_utils import TokenManager, AuditLogger
from shared.dependencies import get_current_user
from users.infrastructure.repositories import UsuarioRepository

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ============ SCHEMAS ============
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    user: dict


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class RefreshTokenResponse(BaseModel):
    access_token: str
    token_type: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


# ============ ENDPOINTS ============

@router.post("/login", response_model=LoginResponse)
async def login(
        credentials: LoginRequest,
        request: Request,
        db: Session = Depends(get_db)
):
    """
    Authenticate user and return access and refresh tokens
    Rate limited to 5 attempts per 5 minutes
    """
    client_ip = request.client.host if request.client else "unknown"
    email = credentials.email.lower()

    # Check rate limit
    allowed, info = AUTH_LIMITER.is_allowed(f"auth:{email}")
    if not allowed:
        AuditLogger.log_action(
            user_id=0,
            action="login_attempt",
            resource="auth",
            status="rate_limited",
            details={"email": email},
            ip_address=client_ip
        )

        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Try again later.",
            headers={
                "X-RateLimit-Reset": info["reset_at"],
                "Retry-After": str(info["window_seconds"])
            }
        )

    # Find user
    repo = UsuarioRepository(db)
    usuario = repo.get_by_email(email)

    if not usuario:
        # Log failed attempt (don't reveal if user exists)
        AuditLogger.log_action(
            user_id=0,
            action="login_attempt",
            resource="auth",
            status="failed",
            details={"email": email, "reason": "user_not_found"},
            ip_address=client_ip
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Verify password
    if not pwd_context.verify(credentials.password, usuario.password or ""):
        # Log failed attempt
        AuditLogger.log_action(
            user_id=usuario.id_usuario,
            action="login_attempt",
            resource="auth",
            status="failed",
            details={"reason": "invalid_password"},
            ip_address=client_ip
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Check if user is active
    if usuario.estado != "Activo":
        AuditLogger.log_action(
            user_id=usuario.id_usuario,
            action="login_attempt",
            resource="auth",
            status="failed",
            details={"reason": "user_inactive"},
            ip_address=client_ip
        )

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    # Create tokens
    access_token = TokenManager.create_access_token(
        user_id=usuario.id_usuario,
        email=usuario.email,
        role_id=usuario.id_rol
    )

    refresh_token = TokenManager.create_refresh_token(usuario.id_usuario)

    # Log successful login
    AuditLogger.log_action(
        user_id=usuario.id_usuario,
        action="login_success",
        resource="auth",
        status="success",
        ip_address=client_ip
    )

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user={
            "id": usuario.id_usuario,
            "nombre": usuario.nombre,
            "apellido": usuario.apellido,
            "email": usuario.email,
            "primer_login": usuario.primer_login,
            "id_rol": usuario.id_rol
        }
    )


@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_access_token(
        request_data: RefreshTokenRequest,
        db: Session = Depends(get_db)
):
    """
    Generate new access token using refresh token
    """
    try:
        payload = TokenManager.verify_token(request_data.refresh_token, token_type="refresh")
        user_id = int(payload.get("sub"))

        # Get user
        repo = UsuarioRepository(db)
        usuario = repo.get_by_id(db, user_id)

        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )

        # Create new access token
        access_token = TokenManager.create_access_token(
            user_id=usuario.id_usuario,
            email=usuario.email,
            role_id=usuario.id_rol
        )

        return RefreshTokenResponse(
            access_token=access_token,
            token_type="bearer"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


@router.post("/logout")
async def logout(
        current_user: dict = Depends(get_current_user),
        request: Request = None
):
    """
    Logout user (log the action for audit)
    Note: JWT tokens are stateless, so actual logout is handled client-side
    """
    client_ip = request.client.host if request.client else current_user.get("ip_address")

    AuditLogger.log_action(
        user_id=current_user["user_id"],
        action="logout",
        resource="auth",
        status="success",
        ip_address=client_ip
    )

    return {
        "message": "Successfully logged out",
        "timestamp": str(AuditLogger.audit_log[-1]["timestamp"] if AuditLogger.audit_log else "")
    }


@router.post("/change-password")
async def change_password(
        password_data: ChangePasswordRequest,
        current_user: dict = Depends(get_current_user),
        request: Request = None,
        db: Session = Depends(get_db)
):
    """
    Change user password
    Requires current password verification
    """
    client_ip = request.client.host if request.client else current_user.get("ip_address")
    user_id = current_user["user_id"]

    # Get user
    repo = UsuarioRepository(db)
    usuario = repo.get_by_id(db, user_id)

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Verify current password
    if not pwd_context.verify(password_data.current_password, usuario.password or ""):
        AuditLogger.log_action(
            user_id=user_id,
            action="change_password_attempt",
            resource="auth",
            status="failed",
            details={"reason": "invalid_current_password"},
            ip_address=client_ip
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect"
        )

    # Validate new password
    if len(password_data.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 8 characters long"
        )

    # Update password
    usuario.password = pwd_context.hash(password_data.new_password)
    repo.update(db, usuario)

    # Log successful password change
    AuditLogger.log_action(
        user_id=user_id,
        action="change_password_success",
        resource="auth",
        status="success",
        ip_address=client_ip
    )

    return {
        "message": "Password changed successfully",
        "timestamp": str(AuditLogger.audit_log[-1]["timestamp"] if AuditLogger.audit_log else "")
    }


@router.get("/me")
async def get_current_user_info(
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Get current user information
    """
    repo = UsuarioRepository(db)
    usuario = repo.get_by_id(db, current_user["user_id"])

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return {
        "id": usuario.id_usuario,
        "nombre": usuario.nombre,
        "apellido": usuario.apellido,
        "email": usuario.email,
        "estado": usuario.estado,
        "id_rol": usuario.id_rol,
        "primer_login": usuario.primer_login,
        "fecha_creacion": usuario.fecha_creacion
    }


@router.get("/audit-log")
async def get_audit_log(
        limit: int = 100,
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Get audit log for current user (admin can see all)
    """
    from shared.security_utils import PermissionChecker

    if PermissionChecker.is_admin(current_user["id_rol"]):
        # Admin sees all logs
        log = AuditLogger.get_audit_log(limit=limit)
    else:
        # Regular user sees only their own logs
        log = AuditLogger.get_audit_log(user_id=current_user["user_id"], limit=limit)

    return {
        "count": len(log),
        "entries": log
    }