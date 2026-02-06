"""
FastAPI middleware for security, rate limiting, and logging
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from datetime import datetime
import time
import logging
from typing import Callable

from shared.rate_limiter import GLOBAL_LIMITER, IP_LIMITER

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("esthervital_api")


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware para implementar rate limiting global e por IP
    """

    def __init__(self, app, global_limit: int = 1000, ip_limit: int = 500):
        super().__init__(app)
        self.global_limit = global_limit
        self.ip_limit = ip_limit

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"

        # Check global rate limit
        global_allowed, global_info = GLOBAL_LIMITER.is_allowed("global")
        if not global_allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded (global)",
                    "message": "Too many requests globally. Please try again later.",
                    "retry_after": global_info["reset_at"]
                }
            )

        # Check IP rate limit
        ip_allowed, ip_info = IP_LIMITER.is_allowed(f"ip:{client_ip}")
        if not ip_allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded (IP)",
                    "message": f"Too many requests from IP {client_ip}",
                    "retry_after": ip_info["reset_at"]
                },
                headers={
                    "X-RateLimit-Limit": str(ip_info["limit"]),
                    "X-RateLimit-Remaining": str(ip_info["remaining"]),
                    "X-RateLimit-Reset": ip_info["reset_at"],
                    "Retry-After": str(ip_info["window_seconds"])
                }
            )

        # Add rate limit headers
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(ip_info["limit"])
        response.headers["X-RateLimit-Remaining"] = str(ip_info["remaining"])
        response.headers["X-RateLimit-Reset"] = ip_info["reset_at"]

        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware para agregar headers de seguridad
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        return response


class CacheControlMiddleware(BaseHTTPMiddleware):
    """
    Middleware para agregar Cache-Control headers basados en el tipo de endpoint.
    - Roles/permisos: cached 5 min (datos semi-estáticos)
    - Mutaciones (POST/PUT/DELETE): no-store
    - GETs de API: no-cache (SWR maneja cache del lado del cliente)
    """

    CACHEABLE_PATHS = {
        "/usuarios/roles": 300,       # 5 minutos
        "/usuarios/permisos": 300,    # 5 minutos
    }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        method = request.method.upper()
        path = request.url.path.rstrip("/")

        # Mutaciones nunca se cachean
        if method in ("POST", "PUT", "DELETE", "PATCH"):
            response.headers["Cache-Control"] = "no-store"
            return response

        # Paths semi-estáticos con max-age
        for cacheable_path, max_age in self.CACHEABLE_PATHS.items():
            if path.endswith(cacheable_path.rstrip("/")):
                response.headers["Cache-Control"] = f"public, max-age={max_age}, stale-while-revalidate=60"
                return response

        # GET de API: no-cache (el cliente SWR se encarga del caching)
        if method == "GET" and ("/usuarios" in path or "/pacientes" in path or "/citas" in path or "/tratamientos" in path or "/historiales" in path):
            response.headers["Cache-Control"] = "no-cache"

        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware para logging de requests y responses
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip logging for health check endpoints
        if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)

        # Capture start time
        start_time = time.time()

        # Get client IP
        client_ip = request.client.host if request.client else "unknown"

        # Process request
        response = await call_next(request)

        # Calculate processing time
        process_time = time.time() - start_time

        # Log request
        log_message = (
            f"{request.method} {request.url.path} | "
            f"Status: {response.status_code} | "
            f"IP: {client_ip} | "
            f"Time: {process_time:.3f}s"
        )

        if response.status_code >= 400:
            logger.warning(log_message)
        else:
            logger.info(log_message)

        # Add processing time header
        response.headers["X-Process-Time"] = str(process_time)

        return response


class IPWhitelistMiddleware(BaseHTTPMiddleware):
    """
    Middleware para whitelist de IPs (opcional)
    Configurar en .env: ALLOWED_IPS=192.168.1.1,10.0.0.1
    """

    def __init__(self, app, allowed_ips: list = None, excluded_paths: list = None):
        super().__init__(app)
        self.allowed_ips = allowed_ips or []
        self.excluded_paths = excluded_paths or ["/health", "/docs", "/redoc"]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip whitelist check for excluded paths
        if request.url.path in self.excluded_paths:
            return await call_next(request)

        # If whitelist is empty, allow all
        if not self.allowed_ips:
            return await call_next(request)

        client_ip = request.client.host if request.client else None

        if client_ip not in self.allowed_ips:
            return JSONResponse(
                status_code=403,
                content={
                    "error": "Forbidden",
                    "message": f"IP {client_ip} is not whitelisted"
                }
            )

        return await call_next(request)


class CORSEnhancedMiddleware(BaseHTTPMiddleware):
    """
    Enhanced CORS middleware with additional security checks
    """

    def __init__(self, app, allowed_origins: list = None):
        super().__init__(app)
        self.allowed_origins = allowed_origins or []

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.method == "OPTIONS":
            return Response(
                status_code=200,
                headers={
                    "Access-Control-Allow-Origin": ", ".join(self.allowed_origins),
                    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, PATCH, OPTIONS",
                    "Access-Control-Allow-Headers": "Content-Type, Authorization",
                    "Access-Control-Max-Age": "600",
                }
            )

        response = await call_next(request)

        origin = request.headers.get("origin")
        if origin in self.allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"

        return response