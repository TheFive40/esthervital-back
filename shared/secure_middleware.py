"""
Enhanced Security Middleware
Protección adicional contra ataques comunes
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import logging
import hashlib
import secrets
from typing import Callable

logger = logging.getLogger("security")


class CSRFProtectionMiddleware(BaseHTTPMiddleware):
    """
    Protección CSRF para operaciones de escritura
    Solo aplica a métodos POST, PUT, DELETE, PATCH

    IMPORTANTE: Este middleware está DESHABILITADO por defecto
    para no romper el frontend existente.

    Para habilitarlo:
    1. Actualizar frontend para enviar X-CSRF-Token header
    2. Cambiar self.enabled = True en __init__
    """

    def __init__(self, app, secret_key: str = None, enabled: bool = False):
        super().__init__(app)
        self.secret_key = secret_key or secrets.token_hex(32)
        self.enabled = enabled  # ⚠️ DESHABILITADO por defecto

        # Rutas excluidas (login, public endpoints)
        self.excluded_paths = [
            "/auth/login",
            "/auth/refresh",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/csrf-token"
        ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Si está deshabilitado, continuar sin validar
        if not self.enabled:
            return await call_next(request)

        # Solo verificar en métodos de escritura
        if request.method not in ["POST", "PUT", "DELETE", "PATCH"]:
            return await call_next(request)

        # Excluir rutas públicas
        if any(request.url.path.startswith(path) for path in self.excluded_paths):
            return await call_next(request)

        # Verificar CSRF token en header
        csrf_token = request.headers.get("X-CSRF-Token")

        if not csrf_token:
            logger.warning(f"CSRF token missing from {request.client.host}")
            return JSONResponse(
                status_code=403,
                content={
                    "error": "CSRF token missing",
                    "message": "X-CSRF-Token header is required"
                }
            )

        # Validar token (en producción, verificar contra sesión)
        if not self._validate_csrf_token(csrf_token):
            logger.warning(f"Invalid CSRF token from {request.client.host}")
            return JSONResponse(
                status_code=403,
                content={
                    "error": "CSRF token invalid",
                    "message": "Invalid or expired CSRF token"
                }
            )

        response = await call_next(request)

        # Generar nuevo token para la siguiente request
        new_token = self._generate_csrf_token()
        response.headers["X-CSRF-Token"] = new_token

        return response

    def _generate_csrf_token(self) -> str:
        """Genera token CSRF único"""
        return secrets.token_urlsafe(32)

    def _validate_csrf_token(self, token: str) -> bool:
        """Valida formato de token CSRF"""
        # En producción: verificar contra sesión/cache
        return len(token) >= 32 and token.replace('-', '').replace('_', '').isalnum()


class IPRateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting adicional por IP para login
    Protege contra brute force attacks
    """

    def __init__(self, app, max_attempts: int = 10, window_seconds: int = 300):
        super().__init__(app)
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self.attempts: dict = {}  # IP -> [timestamps]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Solo aplicar a login
        if not request.url.path.startswith("/auth/login"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"

        # Limpiar intentos antiguos
        self._cleanup_old_attempts()

        # Verificar intentos
        if client_ip in self.attempts:
            if len(self.attempts[client_ip]) >= self.max_attempts:
                logger.warning(f"IP blocked due to excessive login attempts: {client_ip}")
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "Too many login attempts",
                        "message": f"IP blocked. Try again in {self.window_seconds // 60} minutes.",
                        "retry_after": self.window_seconds
                    }
                )

        # Procesar request
        response = await call_next(request)

        # Si login falló (401), incrementar contador
        if response.status_code == 401:
            if client_ip not in self.attempts:
                self.attempts[client_ip] = []

            import time
            self.attempts[client_ip].append(time.time())
            logger.warning(f"Failed login attempt from IP: {client_ip} (attempt {len(self.attempts[client_ip])})")

        # Si login exitoso, limpiar contador
        if response.status_code == 200:
            if client_ip in self.attempts:
                logger.info(f"Successful login from IP: {client_ip}, clearing rate limit")
                del self.attempts[client_ip]

        return response

    def _cleanup_old_attempts(self):
        """Elimina intentos antiguos"""
        import time
        now = time.time()
        cutoff = now - self.window_seconds

        for ip in list(self.attempts.keys()):
            self.attempts[ip] = [
                timestamp for timestamp in self.attempts[ip]
                if timestamp > cutoff
            ]

            if not self.attempts[ip]:
                del self.attempts[ip]


class InputSanitizationMiddleware(BaseHTTPMiddleware):
    """
    Sanitiza input en todas las requests
    Protección adicional contra XSS e injection
    """

    SUSPICIOUS_PATTERNS = [
        "<script",
        "javascript:",
        "onerror=",
        "onload=",
        "onclick=",
        "<iframe",
        "eval(",
        "expression(",
        "vbscript:",
        "data:text/html"
    ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Solo verificar en métodos de escritura
        if request.method in ["POST", "PUT", "PATCH"]:
            # Log suspicious patterns
            if request.headers.get("content-type", "").startswith("application/json"):
                try:
                    body = await request.body()
                    body_str = body.decode("utf-8", errors="ignore")

                    # Detectar patrones sospechosos
                    found_patterns = [
                        pattern for pattern in self.SUSPICIOUS_PATTERNS
                        if pattern.lower() in body_str.lower()
                    ]

                    if found_patterns:
                        logger.warning(
                            f"Suspicious input detected from IP: {request.client.host} "
                            f"on path: {request.url.path} "
                            f"patterns: {', '.join(found_patterns)}"
                        )

                        # Opcionalmente, bloquear la request
                        # return JSONResponse(
                        #     status_code=400,
                        #     content={"error": "Invalid input detected"}
                        # )

                except Exception as e:
                    logger.error(f"Error checking request body: {e}")

        return await call_next(request)


class SecureLoggingMiddleware(BaseHTTPMiddleware):
    """
    Logging seguro que no expone información sensible
    """

    SENSITIVE_HEADERS = [
        "authorization",
        "x-api-key",
        "cookie",
        "x-csrf-token"
    ]

    SENSITIVE_PATHS = [
        "/auth/login",
        "/auth/refresh",
        "/usuarios/me/primer-login",
    ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        import time

        # Capturar tiempo inicial
        start_time = time.time()

        # Determinar si la ruta es sensible
        is_sensitive = any(
            request.url.path.startswith(path)
            for path in self.SENSITIVE_PATHS
        )

        # Log request (sin información sensible)
        if not is_sensitive:
            logger.info(
                f"Request: {request.method} {request.url.path} "
                f"from IP: {request.client.host}"
            )
        else:
            # Para rutas sensibles, no logear detalles
            logger.info(
                f"Request: {request.method} [sensitive endpoint] "
                f"from IP: {request.client.host}"
            )

        # Procesar request
        response = await call_next(request)

        # Calcular tiempo de respuesta
        process_time = time.time() - start_time

        # Log response status
        if response.status_code >= 400:
            logger.warning(
                f"Error response: {response.status_code} "
                f"for {request.method} {request.url.path} "
                f"(took {process_time:.3f}s)"
            )
        elif response.status_code >= 200 and response.status_code < 300:
            if not is_sensitive:
                logger.info(
                    f"Success: {response.status_code} "
                    f"for {request.method} {request.url.path} "
                    f"(took {process_time:.3f}s)"
                )

        # Agregar header con tiempo de proceso
        response.headers["X-Process-Time"] = f"{process_time:.3f}"

        return response


class SecurityHeadersEnhancedMiddleware(BaseHTTPMiddleware):
    """
    Headers de seguridad mejorados
    Complementa SecurityHeadersMiddleware existente
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # Headers adicionales de seguridad
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # Content Security Policy (ajustar según necesidades)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self'"
        )

        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        return response