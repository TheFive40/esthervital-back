"""
Supabase Admin Client
Gestiona interacción con Supabase Auth (creación/eliminación de usuarios)
"""

import os
import requests
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE = os.getenv("SUPABASE_SERVICE_ROLE")


class SupabaseAdminError(Exception):
    """
    Excepción personalizada para errores de Supabase Admin
    """

    def __init__(self, message: str, status_code: int = None, response: Dict = None):
        self.message = message
        self.status_code = status_code
        self.response = response
        super().__init__(self.message)

    def __str__(self):
        if self.status_code:
            return f"SupabaseAdminError ({self.status_code}): {self.message}"
        return f"SupabaseAdminError: {self.message}"


class SupabaseClient:
    """
    Cliente para administración de Supabase Auth
    Requiere SUPABASE_URL y SUPABASE_SERVICE_ROLE configurados en .env
    """

    def __init__(self, url: str = None, service_role: str = None):
        """
        Inicializar cliente Supabase

        Args:
            url: URL de Supabase (si no, usa SUPABASE_URL de env)
            service_role: Service role key (si no, usa SUPABASE_SERVICE_ROLE de env)
        """
        self.url = url or SUPABASE_URL
        self.service_role = service_role or SUPABASE_SERVICE_ROLE

        if not self.url or not self.service_role:
            logger.warning(
                "Supabase credentials not configured. "
                "Set SUPABASE_URL and SUPABASE_SERVICE_ROLE in .env"
            )

    def _get_headers(self) -> Dict[str, str]:
        """Obtener headers para requests de admin"""
        return {
            "apikey": self.service_role,
            "Authorization": f"Bearer {self.service_role}",
            "Content-Type": "application/json",
        }

    def create_user(
            self,
            email: str,
            password: str,
            user_metadata: Optional[Dict[str, Any]] = None,
            email_confirm: bool = True
    ) -> Dict[str, Any]:
        """
        Crear usuario en Supabase Auth

        Args:
            email: Email del usuario
            password: Contraseña del usuario
            user_metadata: Metadatos adicionales (nombre, apellido, etc)
            email_confirm: Si el email está verificado automáticamente

        Returns:
            Dict con información del usuario creado (incluyendo id/uid)

        Raises:
            SupabaseAdminError: Si hay error en la creación
        """
        if not self.url or not self.service_role:
            raise SupabaseAdminError(
                "Supabase credentials not configured (SUPABASE_URL / SUPABASE_SERVICE_ROLE)"
            )

        url = f"{self.url.rstrip('/')}/auth/v1/admin/users"
        headers = self._get_headers()

        payload = {
            "email": email.lower(),
            "password": password,
            "email_confirm": email_confirm
        }

        if user_metadata:
            payload["user_metadata"] = user_metadata

        try:
            logger.info(f"Creating Supabase user: {email}")

            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=10
            )

            if response.status_code >= 400:
                try:
                    error_data = response.json()
                    error_msg = error_data.get("message") or error_data.get("error_description") or str(error_data)
                except Exception:
                    error_msg = response.text

                logger.error(f"Supabase error ({response.status_code}): {error_msg}")

                raise SupabaseAdminError(
                    f"Supabase error: {error_msg}",
                    status_code=response.status_code,
                    response=error_data if 'error_data' in locals() else None
                )

            result = response.json()
            logger.info(f"User created successfully: {email}")
            return result

        except requests.RequestException as e:
            logger.error(f"HTTP error creating Supabase user: {e}")
            raise SupabaseAdminError(f"HTTP error creating Supabase user: {e}")
        except Exception as e:
            logger.error(f"Unexpected error creating Supabase user: {e}")
            raise SupabaseAdminError(f"Unexpected error: {e}")

    def delete_user(self, user_id: str) -> None:
        """
        Eliminar usuario de Supabase Auth

        Args:
            user_id: UID del usuario a eliminar

        Raises:
            SupabaseAdminError: Si hay error en la eliminación
        """
        if not self.url or not self.service_role:
            raise SupabaseAdminError(
                "Supabase credentials not configured"
            )

        url = f"{self.url.rstrip('/')}/auth/v1/admin/users/{user_id}"
        headers = self._get_headers()

        try:
            logger.info(f"Deleting Supabase user: {user_id}")

            response = requests.delete(
                url,
                headers=headers,
                timeout=10
            )

            if response.status_code >= 400:
                try:
                    error_data = response.json()
                    error_msg = error_data.get("message") or str(error_data)
                except Exception:
                    error_msg = response.text

                logger.error(f"Supabase error ({response.status_code}): {error_msg}")

                raise SupabaseAdminError(
                    f"Supabase error: {error_msg}",
                    status_code=response.status_code
                )

            logger.info(f"User deleted successfully: {user_id}")
            return None

        except requests.RequestException as e:
            logger.error(f"HTTP error deleting Supabase user: {e}")
            raise SupabaseAdminError(f"HTTP error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error deleting Supabase user: {e}")
            raise SupabaseAdminError(f"Unexpected error: {e}")

    def get_user(self, user_id: str) -> Dict[str, Any]:
        """
        Obtener información de usuario

        Args:
            user_id: UID del usuario

        Returns:
            Dict con información del usuario

        Raises:
            SupabaseAdminError: Si hay error
        """
        if not self.url or not self.service_role:
            raise SupabaseAdminError(
                "Supabase credentials not configured"
            )

        url = f"{self.url.rstrip('/')}/auth/v1/admin/users/{user_id}"
        headers = self._get_headers()

        try:
            response = requests.get(
                url,
                headers=headers,
                timeout=10
            )

            if response.status_code >= 400:
                raise SupabaseAdminError(
                    f"Supabase error ({response.status_code})",
                    status_code=response.status_code
                )

            return response.json()

        except requests.RequestException as e:
            logger.error(f"HTTP error getting Supabase user: {e}")
            raise SupabaseAdminError(f"HTTP error: {e}")

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Buscar usuario por email (lista y filtra)
        Nota: Supabase no tiene endpoint directo, debe paginar

        Args:
            email: Email a buscar

        Returns:
            Dict del usuario o None si no existe

        Raises:
            SupabaseAdminError: Si hay error
        """
        if not self.url or not self.service_role:
            logger.warning("Supabase credentials not configured")
            return None

        url = f"{self.url.rstrip('/')}/auth/v1/admin/users"
        headers = self._get_headers()

        try:
            response = requests.get(
                url,
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                users = data.get("users", [])

                # Buscar usuario por email
                email_lower = email.lower()
                for user in users:
                    if user.get("email", "").lower() == email_lower:
                        return user

            return None

        except Exception as e:
            logger.error(f"Error searching Supabase user by email: {e}")
            return None

    def update_user_password(self, user_id: str, new_password: str) -> None:
        """
        Actualizar contraseña de usuario

        Args:
            user_id: UID del usuario
            new_password: Nueva contraseña

        Raises:
            SupabaseAdminError: Si hay error
        """
        if not self.url or not self.service_role:
            raise SupabaseAdminError(
                "Supabase credentials not configured"
            )

        url = f"{self.url.rstrip('/')}/auth/v1/admin/users/{user_id}"
        headers = self._get_headers()
        payload = {"password": new_password}

        try:
            logger.info(f"Updating password for user: {user_id}")

            response = requests.put(
                url,
                json=payload,
                headers=headers,
                timeout=10
            )

            if response.status_code >= 400:
                try:
                    error_data = response.json()
                    error_msg = error_data.get("message") or str(error_data)
                except Exception:
                    error_msg = response.text

                logger.error(f"Supabase error ({response.status_code}): {error_msg}")

                raise SupabaseAdminError(
                    f"Supabase error: {error_msg}",
                    status_code=response.status_code
                )

            logger.info(f"Password updated successfully: {user_id}")

        except requests.RequestException as e:
            logger.error(f"HTTP error updating password: {e}")
            raise SupabaseAdminError(f"HTTP error: {e}")

    def update_user_metadata(
            self,
            user_id: str,
            user_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Actualizar metadatos del usuario

        Args:
            user_id: UID del usuario
            user_metadata: Metadatos a actualizar

        Returns:
            Info del usuario actualizado

        Raises:
            SupabaseAdminError: Si hay error
        """
        if not self.url or not self.service_role:
            raise SupabaseAdminError(
                "Supabase credentials not configured"
            )

        url = f"{self.url.rstrip('/')}/auth/v1/admin/users/{user_id}"
        headers = self._get_headers()
        payload = {"user_metadata": user_metadata}

        try:
            logger.info(f"Updating metadata for user: {user_id}")

            response = requests.put(
                url,
                json=payload,
                headers=headers,
                timeout=10
            )

            if response.status_code >= 400:
                raise SupabaseAdminError(
                    f"Supabase error ({response.status_code})",
                    status_code=response.status_code
                )

            logger.info(f"Metadata updated successfully: {user_id}")
            return response.json()

        except requests.RequestException as e:
            logger.error(f"HTTP error updating metadata: {e}")
            raise SupabaseAdminError(f"HTTP error: {e}")


# Funciones wrapper para compatibilidad hacia atrás
def create_user(
        email: str,
        password: str,
        user_metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Wrapper para compatibilidad. Usar SupabaseClient directamente."""
    client = SupabaseClient()
    return client.create_user(email, password, user_metadata)


def delete_user(user_id: str) -> None:
    """Wrapper para compatibilidad. Usar SupabaseClient directamente."""
    client = SupabaseClient()
    return client.delete_user(user_id)


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Wrapper para compatibilidad. Usar SupabaseClient directamente."""
    client = SupabaseClient()
    return client.get_user_by_email(email)


def update_user_password(user_id: str, new_password: str) -> None:
    """Wrapper para compatibilidad. Usar SupabaseClient directamente."""
    client = SupabaseClient()
    return client.update_user_password(user_id, new_password)