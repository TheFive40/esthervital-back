"""
Enhanced Input Validation and Sanitization
Protección completa contra XSS, SQL Injection, Command Injection, Path Traversal
"""

import re
import html
import unicodedata
from typing import Any, Optional, List
from fastapi import HTTPException, status


class InputValidator:
    """
    Validador y sanitizador de entrada de datos
    Protege contra XSS, SQL Injection, Command Injection, Path Traversal
    """

    # ============================================
    # PATRONES DE ATAQUE - SQL INJECTION
    # ============================================
    SQL_INJECTION_PATTERNS = [
        # Comandos SQL básicos
        r"(\bUNION\b.*\bSELECT\b)",
        r"(\bSELECT\b.*\bFROM\b)",
        r"(\bINSERT\b.*\bINTO\b)",
        r"(\bUPDATE\b.*\bSET\b)",
        r"(\bDELETE\b.*\bFROM\b)",
        r"(\bDROP\b.*\b(TABLE|DATABASE|SCHEMA)\b)",
        r"(\bCREATE\b.*\b(TABLE|DATABASE|USER)\b)",
        r"(\bALTER\b.*\bTABLE\b)",
        r"(\bTRUNCATE\b.*\bTABLE\b)",
        r"(\bEXEC\b.*\()",
        r"(\bEXECUTE\b.*\()",

        # Comentarios SQL
        r"(--[^\n]*)",
        r"(\/\*.*?\*\/)",
        r"(\#[^\n]*)",
        r"(;.*--)",

        # Condiciones siempre verdaderas
        r"(\bOR\b\s+['\"]?\w+['\"]?\s*=\s*['\"]?\w+['\"]?)",
        r"(\bAND\b\s+['\"]?\w+['\"]?\s*=\s*['\"]?\w+['\"]?)",
        r"(\bOR\b\s+1\s*=\s*1)",
        r"(\bOR\b\s+'1'\s*=\s*'1')",
        r"(\bAND\b\s+1\s*=\s*1)",

        # Caracteres peligrosos
        r"(['\"];)",
        r"(\\x[0-9a-fA-F]{2})",  # Hex encoding
        r"(%[0-9a-fA-F]{2}){2,}",  # URL encoding múltiple

        # Funciones SQL comunes en ataques
        r"(\bCONCAT\b.*\()",
        r"(\bCHAR\b.*\()",
        r"(\bASCII\b.*\()",
        r"(\bSUBSTRING\b.*\()",
        r"(\bBENCHMARK\b.*\()",
        r"(\bSLEEP\b.*\()",
        r"(\bWAITFOR\b.*\bDELAY\b)",

        # Time-based blind SQL injection
        r"(pg_sleep\(\d+\))",
        r"(SLEEP\(\d+\))",

        # Boolean-based blind SQL injection
        r"(\bIF\b.*\bTHEN\b)",
        r"(\bCASE\b.*\bWHEN\b)",

        # Stacked queries
        r"(;\s*SELECT)",
        r"(;\s*INSERT)",
        r"(;\s*UPDATE)",
        r"(;\s*DELETE)",
        r"(;\s*DROP)",
    ]

    # ============================================
    # PATRONES DE ATAQUE - COMMAND INJECTION
    # ============================================
    COMMAND_INJECTION_PATTERNS = [
        r"(\||&|;|\$\(|\`|<|>)",
        r"(&&|\|\|)",
        r"(\bcat\b|\brm\b|\bwget\b|\bcurl\b|\bchmod\b)",
        r"(\bsh\b|\bbash\b|\bpowershell\b|\bcmd\b)",
        r"(\bnc\b|\bnetcat\b|\bnmap\b)",
        r"(\beval\b|\bexec\b)",
    ]

    # ============================================
    # PATRONES DE ATAQUE - XSS
    # ============================================
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",  # event handlers
        r"<iframe",
        r"<object",
        r"<embed",
        r"<applet",
        r"<meta",
        r"<link",
        r"<style",
        r"<img[^>]+src\s*=\s*['\"]?\s*javascript:",
        r"<svg[^>]*onload\s*=",
        r"data:text/html",
        r"vbscript:",
        r"expression\s*\(",
    ]

    # ============================================
    # PATRONES DE ATAQUE - PATH TRAVERSAL
    # ============================================
    PATH_TRAVERSAL_PATTERNS = [
        r"\.\.",
        r"\.\/",
        r"\.\\",
        r"%2e%2e",
        r"0x2e0x2e",
        r"\x2e\x2e",
    ]

    # ============================================
    # MÉTODOS PÚBLICOS - VALIDACIÓN
    # ============================================

    @staticmethod
    def validate_sql_injection(value: str, strict: bool = True) -> None:
        """
        Valida que no haya patrones de SQL injection

        Args:
            value: String a validar
            strict: Si True, rechaza cualquier patrón sospechoso
                   Si False, solo rechaza patrones claramente maliciosos

        Raises:
            HTTPException: Si detecta SQL injection
        """
        if not isinstance(value, str):
            return

        value_normalized = value.upper().strip()

        # Lista para acumular patrones detectados
        detected_patterns = []

        for pattern in InputValidator.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value_normalized, re.IGNORECASE | re.DOTALL):
                detected_patterns.append(pattern)

        if detected_patterns:
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
            if re.search(pattern, value, re.IGNORECASE | re.DOTALL):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid input: XSS pattern detected"
                )

    @staticmethod
    def validate_path_traversal(value: str) -> None:
        """
        Valida que no haya patrones de path traversal

        Raises:
            HTTPException: Si detecta path traversal
        """
        if not isinstance(value, str):
            return

        for pattern in InputValidator.PATH_TRAVERSAL_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid input: Path traversal pattern detected"
                )

    # ============================================
    # MÉTODOS PÚBLICOS - SANITIZACIÓN
    # ============================================

    @staticmethod
    def sanitize_string(value: str, allow_html: bool = False, max_length: int = None) -> str:
        """
        Sanitiza un string

        Args:
            value: String a sanitizar
            allow_html: Si permite HTML básico (sanitiza pero no elimina)
            max_length: Longitud máxima permitida

        Returns:
            String sanitizado
        """
        if not isinstance(value, str):
            return value

        # Normalizar unicode
        value = unicodedata.normalize('NFKC', value)

        # Eliminar caracteres de control (excepto \n, \r, \t)
        value = ''.join(char for char in value if char in '\n\r\t' or not unicodedata.category(char).startswith('C'))

        value = value.strip()

        if not allow_html:
            # HTML escape completo
            value = html.escape(value)
        else:
            # Eliminar solo HTML peligroso
            value = InputValidator._remove_dangerous_html(value)

        # Limitar longitud si se especifica
        if max_length and len(value) > max_length:
            value = value[:max_length]

        return value

    @staticmethod
    def _remove_dangerous_html(value: str) -> str:
        """Elimina HTML peligroso pero permite básico"""
        # Eliminar scripts
        value = re.sub(r'<script[^>]*>.*?</script>', '', value, flags=re.IGNORECASE | re.DOTALL)

        # Eliminar event handlers (onclick, onerror, etc)
        value = re.sub(r'\s*on\w+\s*=\s*["\'][^"\']*["\']', '', value, flags=re.IGNORECASE)
        value = re.sub(r'\s*on\w+\s*=\s*[^\s>]*', '', value, flags=re.IGNORECASE)

        # Eliminar javascript: y vbscript:
        value = re.sub(r'javascript:', '', value, flags=re.IGNORECASE)
        value = re.sub(r'vbscript:', '', value, flags=re.IGNORECASE)

        # Eliminar iframes, objects, embeds, applets
        value = re.sub(r'<(iframe|object|embed|applet)[^>]*>.*?</\1>', '', value, flags=re.IGNORECASE | re.DOTALL)

        # Eliminar meta refresh
        value = re.sub(r'<meta[^>]*http-equiv[^>]*refresh[^>]*>', '', value, flags=re.IGNORECASE)

        return value

    @staticmethod
    def sanitize_search_term(term: str, max_length: int = 100) -> str:
        """
        Sanitiza un término de búsqueda
        Permite solo caracteres alfanuméricos, espacios y algunos especiales seguros

        Args:
            term: Término de búsqueda
            max_length: Longitud máxima

        Returns:
            Término sanitizado
        """
        if not isinstance(term, str):
            return ""

        # Normalizar unicode
        term = unicodedata.normalize('NFKC', term)

        # Eliminar caracteres peligrosos, permitir solo alfanuméricos, espacios, guiones, puntos
        sanitized = re.sub(r'[^a-zA-Z0-9áéíóúñÁÉÍÓÚÑ\s\-\.\@]', '', term)

        # Eliminar múltiples espacios
        sanitized = re.sub(r'\s+', ' ', sanitized)

        # Limitar longitud
        sanitized = sanitized[:max_length].strip()

        return sanitized

    @staticmethod
    def sanitize_sql_like_pattern(value: str) -> str:
        """
        Sanitiza un valor para uso en LIKE/ILIKE de SQL
        Escapa caracteres especiales de SQL LIKE: % y _

        Args:
            value: Valor a sanitizar

        Returns:
            Valor escapado para SQL LIKE
        """
        if not isinstance(value, str):
            return ""

        value = InputValidator.sanitize_search_term(value)

        value = value.replace('\\', '\\\\')
        value = value.replace('%', '\\%')
        value = value.replace('_', '\\_')

        return value

    @staticmethod
    def validate_all(value: str, allow_html: bool = False, max_length: int = None) -> str:
        """
        Valida y sanitiza un string contra todas las amenazas

        Args:
            value: String a validar
            allow_html: Si permite HTML básico
            max_length: Longitud máxima

        Returns:
            String sanitizado y validado

        Raises:
            HTTPException: Si detecta patrón peligroso
        """
        if not isinstance(value, str):
            return value

        InputValidator.validate_sql_injection(value, strict=False)
        InputValidator.validate_command_injection(value)
        InputValidator.validate_xss(value)
        InputValidator.validate_path_traversal(value)

        return InputValidator.sanitize_string(value, allow_html, max_length)

    @staticmethod
    def validate_email(email: str) -> bool:
        """
        Valida formato de email

        Args:
            email: Email a validar

        Returns:
            True si es válido
        """
        if not email or not isinstance(email, str):
            return False

        email = email.strip().lower()

        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

        if not re.match(pattern, email):
            return False

        local, domain = email.rsplit('@', 1)

        if local.startswith('.') or local.endswith('.'):
            return False

        if '..' in local:
            return False

        # Domain debe tener al menos un punto
        if '.' not in domain:
            return False

        return True

    @staticmethod
    def validate_phone(phone: str, country: str = 'CO') -> bool:
        """
        Valida formato de teléfono

        Args:
            phone: Teléfono a validar
            country: Código de país (CO = Colombia)

        Returns:
            True si es válido
        """
        if not phone or not isinstance(phone, str):
            return False

        # Limpiar formato
        clean_phone = re.sub(r'[\s\-\(\)\+]', '', phone)

        if country == 'CO':
            # Formato colombiano: 3XXXXXXXXX (10 dígitos empezando con 3)
            # O con código de país: 573XXXXXXXXX
            pattern = r'^(\+?57)?3\d{9}$'
            return bool(re.match(pattern, clean_phone))

        return False

    @staticmethod
    def validate_integer_range(value: Any, min_val: int = None, max_val: int = None) -> bool:
        """
        Valida que un valor sea un entero en el rango especificado

        Args:
            value: Valor a validar
            min_val: Valor mínimo (inclusive)
            max_val: Valor máximo (inclusive)

        Returns:
            True si es válido
        """
        try:
            int_value = int(value)

            if min_val is not None and int_value < min_val:
                return False

            if max_val is not None and int_value > max_val:
                return False

            return True
        except (ValueError, TypeError):
            return False

    @staticmethod
    def validate_date_format(date_str: str, format: str = '%Y-%m-%d') -> bool:
        """
        Valida formato de fecha

        Args:
            date_str: String de fecha
            format: Formato esperado

        Returns:
            True si es válido
        """
        if not date_str or not isinstance(date_str, str):
            return False

        from datetime import datetime
        try:
            datetime.strptime(date_str, format)
            return True
        except ValueError:
            return False


# ============================================
# VALIDADOR DE ARCHIVOS
# ============================================

class SecureFileValidator:
    """Validador de archivos subidos"""

    ALLOWED_EXTENSIONS = {
        'image': ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'],
        'document': ['.pdf', '.doc', '.docx', '.txt'],
        'spreadsheet': ['.xls', '.xlsx', '.csv'],
        'all': ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.csv']
    }

    # Límites de tamaño por tipo
    MAX_FILE_SIZE = {
        'image': 10 * 1024 * 1024,      # 10MB
        'document': 25 * 1024 * 1024,   # 25MB
        'spreadsheet': 10 * 1024 * 1024, # 10MB
        'default': 10 * 1024 * 1024      # 10MB
    }

    # Magic bytes para validación de tipo real
    MAGIC_BYTES = {
        '.jpg': [b'\xFF\xD8\xFF'],
        '.jpeg': [b'\xFF\xD8\xFF'],
        '.png': [b'\x89\x50\x4E\x47'],
        '.gif': [b'\x47\x49\x46\x38'],
        '.pdf': [b'\x25\x50\x44\x46'],
        '.webp': [b'\x52\x49\x46\x46'],
    }

    @staticmethod
    def validate_filename(filename: str, max_length: int = 255) -> str:
        """
        Valida y sanitiza nombre de archivo

        Args:
            filename: Nombre del archivo
            max_length: Longitud máxima

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

        # Validar path traversal
        InputValidator.validate_path_traversal(filename)

        # Eliminar path separators
        filename = filename.replace('..', '').replace('/', '').replace('\\', '')

        # Permitir solo caracteres seguros
        # Letras, números, guión, guión bajo, punto
        filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)

        # No permitir nombres que empiecen con punto (archivos ocultos)
        if filename.startswith('.'):
            filename = '_' + filename[1:]

        # Limitar longitud
        if len(filename) > max_length:
            # Mantener extensión
            name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
            max_name_length = max_length - len(ext) - 1
            filename = name[:max_name_length] + '.' + ext if ext else name[:max_length]

        return filename

    @staticmethod
    def validate_file_extension(
        filename: str,
        allowed_type: str = 'all',
        case_sensitive: bool = False
    ) -> None:
        """
        Valida extensión de archivo

        Args:
            filename: Nombre del archivo
            allowed_type: Tipo permitido ('image', 'document', 'spreadsheet', 'all')
            case_sensitive: Si la validación es case-sensitive

        Raises:
            HTTPException: Si la extensión no está permitida
        """
        if '.' not in filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must have an extension"
            )

        ext = '.' + filename.rsplit('.', 1)[-1]

        if not case_sensitive:
            ext = ext.lower()

        allowed = SecureFileValidator.ALLOWED_EXTENSIONS.get(allowed_type, [])

        if ext not in allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type not allowed. Allowed extensions: {', '.join(allowed)}"
            )

    @staticmethod
    def validate_file_size(size: int, file_type: str = 'default') -> None:
        """
        Valida tamaño de archivo

        Args:
            size: Tamaño en bytes
            file_type: Tipo de archivo para determinar límite

        Raises:
            HTTPException: Si excede el tamaño máximo
        """
        max_size = SecureFileValidator.MAX_FILE_SIZE.get(
            file_type,
            SecureFileValidator.MAX_FILE_SIZE['default']
        )

        if size > max_size:
            max_mb = max_size / (1024 * 1024)
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size: {max_mb:.1f}MB"
            )

    @staticmethod
    def validate_file_content(content: bytes, filename: str) -> None:
        """
        Valida que el contenido del archivo coincida con su extensión
        usando magic bytes

        Args:
            content: Contenido del archivo
            filename: Nombre del archivo

        Raises:
            HTTPException: Si el contenido no coincide con la extensión
        """
        if not content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File is empty"
            )

        ext = '.' + filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''

        magic_bytes_list = SecureFileValidator.MAGIC_BYTES.get(ext)

        if magic_bytes_list:
            # Verificar que el archivo empiece con uno de los magic bytes esperados
            is_valid = any(
                content.startswith(magic_bytes)
                for magic_bytes in magic_bytes_list
            )

            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File content does not match extension {ext}"
                )

    @staticmethod
    def validate_file_complete(
        filename: str,
        size: int,
        content: bytes = None,
        file_type: str = 'all'
    ) -> str:
        """
        Validación completa de archivo

        Args:
            filename: Nombre del archivo
            size: Tamaño en bytes
            content: Contenido del archivo (opcional)
            file_type: Tipo de archivo

        Returns:
            Nombre sanitizado

        Raises:
            HTTPException: Si alguna validación falla
        """
        safe_filename = SecureFileValidator.validate_filename(filename)

        SecureFileValidator.validate_file_extension(safe_filename, file_type)

        SecureFileValidator.validate_file_size(size, file_type)

        if content:
            SecureFileValidator.validate_file_content(content, safe_filename)

        return safe_filename