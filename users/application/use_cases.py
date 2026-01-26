"""
Use cases para creación de usuarios con integración Supabase
"""

from users.infrastructure.models import Usuario
from passlib.context import CryptContext
from shared.supabase_client import SupabaseClient, SupabaseAdminError
from typing import Optional

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class CrearUsuarioUseCase:
    """
    Caso de uso para crear usuario

    Flujo:
    1. Crear en Supabase Auth (si está configurado)
    2. Hash de contraseña para BD local
    3. Crear en BD local con auth_id de Supabase
    4. Si falla BD, eliminar de Supabase para evitar huérfanos
    """

    def __init__(self, usuario_repository):
        self.usuario_repository = usuario_repository
        self.supabase = SupabaseClient()

    def execute(self, data) -> Usuario:
        """
        Crear usuario en sistema

        Args:
            data: UsuarioCreate schema

        Returns:
            Usuario creado

        Raises:
            SupabaseAdminError: Si hay error en Supabase
            IntegrityError: Si hay error en BD local
        """
        auth_id = None
        created_in_supabase = False
        email_normalized = data.email.lower()

        # 1) Intentar crear en Supabase si está configurado
        if self.supabase.url and self.supabase.service_role:
            try:
                # Crear en Supabase
                supa_user = self.supabase.create_user(
                    email_normalized,
                    data.password,
                    {
                        "nombre": data.nombre,
                        "apellido": data.apellido
                    }
                )
                auth_id = supa_user.get("id")
                created_in_supabase = True

            except SupabaseAdminError as e:
                msg = str(e).lower()

                # Si el usuario ya existe en Auth, intentar vincularlo
                if "already" in msg or "duplicate" in msg or "exists" in msg:
                    existing = self.supabase.get_user_by_email(email_normalized)
                    if existing:
                        auth_id = existing.get("id")
                        # Actualizar contraseña
                        try:
                            self.supabase.update_user_password(auth_id, data.password)
                        except SupabaseAdminError:
                            # Log error pero continuar
                            pass
                    else:
                        # Usuario no encontrado, propagar error
                        raise e
                else:
                    # Otro error, propagar
                    raise e

        # 2) Hash de contraseña para BD local
        hashed_password = pwd_context.hash(data.password)

        # 3) Crear en BD local
        usuario = Usuario(
            nombre=data.nombre,
            apellido=data.apellido,
            email=email_normalized,
            password=hashed_password,
            auth_id=auth_id,
            id_rol=data.id_rol,
            estado="Activo",
            primer_login=True  # Primer login = debe cambiar contraseña
        )

        # 4) Persistir en BD; si falla, limpiar Supabase
        try:
            return self.usuario_repository.create(usuario)

        except Exception as db_err:
            # Intentar rollback en Supabase SOLO si lo creamos
            if auth_id and created_in_supabase:
                try:
                    self.supabase.delete_user(auth_id)
                except SupabaseAdminError:
                    # Log pero no propagar
                    pass

            raise db_err