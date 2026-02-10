"""
Input Validation and Sanitization
Protección contra XSS, SQL Injection, Command Injection
"""

import re
import html
from typing import Any, Optional
from fastapi import HTTPException, status


class InputValidator:
    """
    Validador y sanitizador de entrada de datos
    Protege contra XSS, SQL Injection, Command Injection
    """

    # Patrones peligrosos
    SQL_INJECTION_PATTERNS = [
        r"(\bUNION\b|\bSELECT\b|\bINSERT\b|\bUPDATE\b|\bDELETE\b|\bDROP\b)",
        r"(--|\#|/\*|\*/)",
        r"(\bOR\b.*=.*|\bAND\b.*=.*)",
        r"(\'|\"|;|\\x)",
    ]

    COMMAND_INJECTION_PATTERNS = [
        r"(\||&|;|\$\(|\`|<|>)",
        r"(&&|\|\|)",
        r"(\bcat\b|\brm\b|\bwget\b|\bcurl\b|\bchmod\b)",
    ]

    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe",
        r"<object",
        r"<embed",
    ]

    @staticmethod
    def sanitize_string(value: str, allow_html: bool = False) -> str:
        """
        Sanitiza un string

        Args:
            value: String a sanitizar
            allow_html: Si permite HTML (sanitiza pero no elimina)

        Returns:
            String sanitizado
        """
        if not isinstance(value, str):
            return value

        value = value.strip()

        if not allow_html:
            value = html.escape(value)
        else:
            value = InputValidator._remove_dangerous_html(value)

        return value

    @staticmethod
    def _remove_dangerous_html(value: str) -> str:
        """Elimina HTML peligroso pero permite básico"""
        # Eliminar scripts
        value = re.sub(r'<script[^>]*>.*?</script>', '', value, flags=re.IGNORECASE | re.DOTALL)

        # Eliminar event handlers
        value = re.sub(r'\son\w+\s*=\s*["\'][^"\']*["\']', '', value, flags=re.IGNORECASE)

        # Eliminar javascript:
        value = re.sub(r'javascript:', '', value, flags=re.IGNORECASE)

        # Eliminar iframes, objects, embeds
        value = re.sub(r'<(iframe|object|embed)[^>]*>.*?</\1>', '', value, flags=re.IGNORECASE | re.DOTALL)

        return value

    @staticmethod
    def validate_sql_injection(value: str) -> None:
        """
        Valida que no haya patrones de SQL injection

        Raises:
            HTTPException: Si detecta SQL injection
        """
        if not isinstance(value, str):
            return

        value_upper = value.upper()

        for pattern in InputValidator.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value_upper, re.IGNORECASE):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid input: SQL injection pattern detected"
                )

    @staticmethod
    def validate_command_injection(value: str) -> None:
        """
        Valida que no haya patrones de command injection

        Raises:
            HTTPException: Si detecta command injection
        """
        if not isinstance(value, str):
            return

        for pattern in InputValidator.COMMAND_INJECTION_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid input: Command injection pattern detected"
                )

    @staticmethod
    def validate_xss(value: str) -> None:
        """
        Valida que no haya patrones de XSS

        Raises:
            HTTPException: Si detecta XSS
        """
        if not isinstance(value, str):
            return

        for pattern in InputValidator.XSS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid input: XSS pattern detected"
                )

    @staticmethod
    def validate_all(value: str, allow_html: bool = False) -> str:
        """
        Valida y sanitiza un string contra todas las amenazas

        Args:
            value: String a validar
            allow_html: Si permite HTML básico

        Returns:
            String sanitizado y validado

        Raises:
            HTTPException: Si detecta patrón peligroso
        """
        if not isinstance(value, str):
            return value

        # Validar inyecciones
        InputValidator.validate_sql_injection(value)
        InputValidator.validate_command_injection(value)
        InputValidator.validate_xss(value)

        # Sanitizar
        return InputValidator.sanitize_string(value, allow_html)

    @staticmethod
    def sanitize_search_term(term: str) -> str:
        """
        Sanitiza un término de búsqueda
        Permite solo caracteres alfanuméricos, espacios y algunos especiales

        Args:
            term: Término de búsqueda

        Returns:
            Término sanitizado
        """
        if not isinstance(term, str):
            return ""

        sanitized = re.sub(r'[^a-zA-Z0-9áéíóúñÁÉÍÓÚÑ\s\-\.]', '', term)

        return sanitized[:100].strip()

    @staticmethod
    def validate_email(email: str) -> bool:
        """
        Valida formato de email (simple)

        Args:
            email: Email a validar

        Returns:
            True si es válido
        """
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    @staticmethod
    def validate_phone(phone: str) -> bool:
        """
        Valida formato de teléfono colombiano

        Args:
            phone: Teléfono a validar

        Returns:
            True si es válido
        """
        pattern = r'^(\+?57)?3\d{9}$'
        clean_phone = re.sub(r'[\s\-\(\)]', '', phone)
        return bool(re.match(pattern, clean_phone))


class SecureFileValidator:
    """Validador de archivos subidos"""

    ALLOWED_EXTENSIONS = {
        'image': ['.jpg', '.jpeg', '.png', '.gif', '.webp'],
        'document': ['.pdf', '.doc', '.docx'],
        'all': ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.pdf', '.doc', '.docx']
    }

    MAX_FILE_SIZE = 10 * 1024 * 1024

    @staticmethod
    def validate_filename(filename: str) -> str:
        """
        Valida y sanitiza nombre de archivo

        Args:
            filename: Nombre del archivo

        Returns:
            Nombre sanitizado

        Raises:
            HTTPException: Si el nombre es inválido
        """
        if not filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Filename is required"
            )

        # Eliminar path traversal
        filename = filename.replace('..', '').replace('/', '').replace('\\', '')

        # Permitir solo caracteres seguros
        filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)

        # Limitar longitud
        if len(filename) > 255:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Filename too long"
            )

        return filename

    @staticmethod
    def validate_file_extension(filename: str, allowed_type: str = 'all') -> None:
        """
        Valida extensión de archivo

        Args:
            filename: Nombre del archivo
            allowed_type: Tipo permitido ('image', 'document', 'all')

        Raises:
            HTTPException: Si la extensión no está permitida
        """
        ext = '.' + filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''

        allowed = SecureFileValidator.ALLOWED_EXTENSIONS.get(allowed_type, [])

        if ext not in allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type not allowed. Allowed: {', '.join(allowed)}"
            )

    @staticmethod
    def validate_file_size(size: int) -> None:
        """
        Valida tamaño de archivo

        Args:
            size: Tamaño en bytes

        Raises:
            HTTPException: Si excede el tamaño máximo
        """
        if size > SecureFileValidator.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Max: {SecureFileValidator.MAX_FILE_SIZE / (1024 * 1024)}MB"
            )