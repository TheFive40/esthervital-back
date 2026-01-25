from users.infrastructure.models import Usuario
from passlib.context import CryptContext
from shared.supabase_client import create_user, delete_user, SupabaseAdminError, get_user_by_email, update_user_password


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class CrearUsuarioUseCase:

    def __init__(self, usuario_repository):
        self.usuario_repository = usuario_repository

    def execute(self, data):
        """Create user in Supabase Auth (admin) and persist user in local DB.

        Flow:
        1. Call Supabase admin create user
        2. Hash password and create local Usuario with `auth_id` from Supabase
        3. If DB insert fails, delete the Supabase user to avoid orphans
        """
        # 1) Create in Supabase or Link Existing
        created_in_supabase = False
        email_normalized = data.email.lower()
        try:
            supa_user = create_user(email_normalized, data.password, {"nombre": data.nombre, "apellido": data.apellido})
            auth_id = supa_user.get("id")
            created_in_supabase = True
        except SupabaseAdminError as e:
            msg = str(e).lower()
            if "already" in msg or "duplicate" in msg or "exists" in msg:
                # User exists in Auth provider. Let's try to link it.
                existing = get_user_by_email(email_normalized)
                if existing:
                    auth_id = existing.get("id")
                    # Update password to match the one provided in this form
                    try:
                        update_user_password(auth_id, data.password)
                    except Exception:
                        # Log error but proceed? Or fail? Let's proceed, user can reset password.
                        pass
                else:
                    # Should not happen unless race condition or pagination limit
                    raise e
            else:
                # Propagate other errors (502, etc)
                raise

        # 2) Hash password for local storage
        hashed = pwd_context.hash(data.password)

        usuario = Usuario(
            nombre=data.nombre,
            apellido=data.apellido,
            email=email_normalized,
            password=hashed,
            auth_id=auth_id,
            id_rol=data.id_rol,
            estado="Activo"
        )

        # 3) Persist in local DB; if fails, remove Supabase user
        try:
            return self.usuario_repository.create(usuario)
        except Exception as db_err:
            # Attempt to rollback Supabase user ONLY if we created it
            try:
                if auth_id and created_in_supabase:
                    delete_user(auth_id)
            except Exception:
                pass
            raise db_err
