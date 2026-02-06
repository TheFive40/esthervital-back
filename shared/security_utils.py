"""
Security utilities for authentication, authorization, and permissions
"""

import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
import os
import requests

from users.infrastructure.models import Usuario
from users.infrastructure.repositories import UsuarioRepository


class TokenManager:
    """Manage JWT token creation and validation"""

    SECRET_KEY = os.getenv("JWT_SECRET", "dev-secret-key-change-in-production")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 hours
    REFRESH_TOKEN_EXPIRE_DAYS = 7
    
    # Supabase configuration
    SUPABASE_URL = os.getenv("SUPABASE_URL", "")
    SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")

    @classmethod
    def create_access_token(cls, user_id: int, email: str, role_id: int) -> str:
        """Create JWT access token"""
        payload = {
            "sub": str(user_id),
            "email": email,
            "role_id": role_id,
            "type": "access",
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(minutes=cls.ACCESS_TOKEN_EXPIRE_MINUTES)
        }
        return jwt.encode(payload, cls.SECRET_KEY, algorithm=cls.ALGORITHM)

    @classmethod
    def create_refresh_token(cls, user_id: int) -> str:
        """Create JWT refresh token"""
        payload = {
            "sub": str(user_id),
            "type": "refresh",
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(days=cls.REFRESH_TOKEN_EXPIRE_DAYS)
        }
        return jwt.encode(payload, cls.SECRET_KEY, algorithm=cls.ALGORITHM)

    @classmethod
    def verify_supabase_token(cls, token: str) -> Dict:
        """Verify token with Supabase and get user info"""
        try:
            # Call Supabase to verify the token and get user data
            response = requests.get(
                f"{cls.SUPABASE_URL}/auth/v1/user",
                headers={
                    "Authorization": f"Bearer {token}",
                    "apikey": cls.SUPABASE_ANON_KEY
                },
                timeout=10
            )
            
            if response.status_code == 200:
                user_data = response.json()
                return {
                    "sub": user_data.get("id"),  # Supabase user UUID
                    "email": user_data.get("email"),
                    "type": "supabase",
                    "supabase_user": user_data
                }
            else:
                return None
        except Exception as e:
            print(f"Supabase token verification error: {e}")
            return None

    @classmethod
    def verify_token(cls, token: str, token_type: str = "access") -> Dict:
        """Verify and decode JWT token (supports both local and Supabase tokens)"""
        # First try to decode as local JWT
        try:
            payload = jwt.decode(token, cls.SECRET_KEY, algorithms=[cls.ALGORITHM])

            if token_type != "refresh" and payload.get("type") != token_type:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token type inválido"
                )

            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expirado"
            )
        except jwt.InvalidTokenError:
            # Token is not a valid local JWT, try Supabase
            if cls.SUPABASE_URL and cls.SUPABASE_ANON_KEY:
                supabase_payload = cls.verify_supabase_token(token)
                if supabase_payload:
                    return supabase_payload
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido"
            )


class PermissionChecker:
    """Check user permissions based on roles"""

    # Define role-based permissions
    ROLE_PERMISSIONS: Dict[int, List[str]] = {
        1: [  # Administrador
            "create_user",
            "read_user",
            "update_user",
            "delete_user",
            "create_patient",
            "read_patient",
            "update_patient",
            "delete_patient",
            "create_appointment",
            "read_appointment",
            "update_appointment",
            "delete_appointment",
            "create_treatment",
            "read_treatment",
            "update_treatment",
            "delete_treatment",
            "create_session",
            "read_session",
            "update_session",
            "delete_session",
            "read_historial",
            "create_historial",
            "update_historial",
            "delete_historial",
            "manage_roles",
            "manage_permissions",
            "view_analytics",
        ],
        2: [  # Empleado
            "read_patient",
            "update_patient",
            "create_appointment",
            "read_appointment",
            "update_appointment",
            "create_treatment",
            "read_treatment",
            "update_treatment",
            "create_session",
            "read_session",
            "update_session",
            "read_historial",
            "create_historial",
            "update_historial",
        ]
    }

    @staticmethod
    def has_permission(user_id: int, permission: str, db: Session) -> bool:
        """Check if user has specific permission"""
        repo = UsuarioRepository(db)
        usuario = repo.get_by_id(db, user_id)

        if not usuario:
            return False

        role_id = usuario.id_rol
        permissions = PermissionChecker.ROLE_PERMISSIONS.get(role_id, [])

        return permission in permissions

    @staticmethod
    def has_any_permission(user_id: int, permissions: List[str], db: Session) -> bool:
        """Check if user has any of the permissions"""
        repo = UsuarioRepository(db)
        usuario = repo.get_by_id(db, user_id)

        if not usuario:
            return False

        role_id = usuario.id_rol
        user_permissions = PermissionChecker.ROLE_PERMISSIONS.get(role_id, [])

        return any(p in user_permissions for p in permissions)

    @staticmethod
    def has_all_permissions(user_id: int, permissions: List[str], db: Session) -> bool:
        """Check if user has all permissions"""
        repo = UsuarioRepository(db)
        usuario = repo.get_by_id(db, user_id)

        if not usuario:
            return False

        role_id = usuario.id_rol
        user_permissions = PermissionChecker.ROLE_PERMISSIONS.get(role_id, [])

        return all(p in user_permissions for p in permissions)

    @staticmethod
    def is_admin(user_id: int, db: Session) -> bool:
        """Check if user is administrator"""
        repo = UsuarioRepository(db)
        usuario = repo.get_by_id(db, user_id)

        if not usuario:
            return False

        return usuario.id_rol == 1

    @staticmethod
    def is_employee(user_id: int, db: Session) -> bool:
        """Check if user is employee"""
        repo = UsuarioRepository(db)
        usuario = repo.get_by_id(db, user_id)

        if not usuario:
            return False

        return usuario.id_rol == 2


class AuditLogger:
    """Log user actions for security audit"""

    # In-memory audit log (in production, save to database)
    audit_log: List[Dict] = []

    @classmethod
    def log_action(
        cls,
        user_id: int,
        action: str,
        resource: str,
        resource_id: Optional[int] = None,
        status: str = "success",
        details: Optional[Dict] = None,
        ip_address: Optional[str] = None
    ) -> None:
        """Log an action"""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "action": action,
            "resource": resource,
            "resource_id": resource_id,
            "status": status,
            "details": details,
            "ip_address": ip_address
        }
        cls.audit_log.append(entry)

        # Keep only last 10000 entries in memory
        if len(cls.audit_log) > 10000:
            cls.audit_log = cls.audit_log[-10000:]

    @classmethod
    def get_audit_log(cls, user_id: Optional[int] = None, limit: int = 100) -> List[Dict]:
        """Get audit log entries"""
        if user_id:
            return [e for e in cls.audit_log if e["user_id"] == user_id][-limit:]
        return cls.audit_log[-limit:]