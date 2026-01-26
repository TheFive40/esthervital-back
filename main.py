from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os

from users.presentation.router import router as usuarios_router
from patients.presentation.router import router as pacientes_router
from historials.presentation.router import router as historiales_router
from appointments.presentation.router import router as citas_router
from treatments.presentation.router import router as tratamientos_router
from shared.auth_router import router as auth_router

from shared.database import Base, engine
from shared.middleware import (
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
    RequestLoggingMiddleware,
    IPWhitelistMiddleware,
    CORSEnhancedMiddleware
)

app = FastAPI(
    title="EstherVital API",
    description="API REST para gestión de estética EstherVital con autenticación y control de acceso",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Create tables
Base.metadata.create_all(bind=engine)

# Configure CORS
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://esthervital-front.vercel.app",
]

# Add middleware stack (ORDER MATTERS - from bottom to top)
# 1. Security headers
app.add_middleware(SecurityHeadersMiddleware)

# 2. Request logging
app.add_middleware(RequestLoggingMiddleware)

# 3. Rate limiting (global and per-IP)
app.add_middleware(RateLimitMiddleware)

# 4. IP Whitelist (if configured)
allowed_ips = os.getenv("ALLOWED_IPS", "").split(",") if os.getenv("ALLOWED_IPS") else []
if allowed_ips and allowed_ips[0]:
    app.add_middleware(IPWhitelistMiddleware, allowed_ips=allowed_ips)

# 5. Enhanced CORS
app.add_middleware(CORSEnhancedMiddleware, allowed_origins=origins)

# Legacy CORS (can be removed if using CORSEnhancedMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============ HEALTH CHECK ENDPOINT ============
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "service": "EstherVital API",
        "version": "2.0.0"
    }


# ============ ERROR HANDLERS ============
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "detail": str(exc) if os.getenv("DEBUG", "false").lower() == "true" else None
        }
    )


# ============ INCLUDE ROUTERS ============
# Auth router should be first (no auth required for login)
app.include_router(auth_router)

# Protected routers
app.include_router(usuarios_router)
app.include_router(pacientes_router)
app.include_router(historiales_router)
app.include_router(citas_router)
app.include_router(tratamientos_router)


# ============ STARTUP EVENT ============
@app.on_event("startup")
async def startup_event():
    """Initialize application"""
    print("✅ EstherVital API iniciado correctamente")
    print("📚 Documentación disponible en: /docs")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("🛑 EstherVital API detenido")