from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging
import os

from users.presentation.router import router as usuarios_router
from patients.presentation.router import router as pacientes_router
from historials.presentation.router import router as historiales_router
from appointments.presentation.router import router as citas_router
from treatments.presentation.router import router as tratamientos_router
from treatments.presentation.payment_router import router as pagos_router
from patients.presentation.consent_router import router as consentimientos_router

from shared.database import Base, engine
from shared.middleware import (
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
    RequestLoggingMiddleware,
    CacheControlMiddleware
)
from shared.secure_middleware import (
    IPRateLimitMiddleware,
    InputSanitizationMiddleware,
    SecureLoggingMiddleware
)
from shared.auth_router import router as auth_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="API EstherVital",
    description="API para gestión de pacientes, historiales, citas y tratamientos - Versión Segura",
    version="2.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

Base.metadata.create_all(bind=engine)

app.add_middleware(SecureLoggingMiddleware)
app.add_middleware(InputSanitizationMiddleware)
app.add_middleware(IPRateLimitMiddleware, max_attempts=10, window_seconds=300)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(CacheControlMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

# --- CORS: build the full origins list BEFORE registering the middleware ---
cors_origins_env = os.getenv("CORS_ORIGINS", "")
origins = cors_origins_env.split(",") if cors_origins_env else [
    "https://esthervital-front.onrender.com/",
    "https://esthervital-front.onrender.com",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

production_origins = [
    "https://esthervital-front.vercel.app",
    "https://esthervital-staging.vercel.app",
]

# Merge production origins BEFORE registering the middleware
for origin in production_origins:
    if origin not in origins:
        origins.append(origin)

# Single CORSMiddleware registration
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
    max_age=600,
)

app.include_router(auth_router)
app.include_router(usuarios_router)
app.include_router(pacientes_router)
app.include_router(historiales_router)
app.include_router(citas_router)
app.include_router(tratamientos_router)
app.include_router(consentimientos_router)
app.include_router(pagos_router)


@app.get("/")
async def root():
    return {
        "message": "EstherVital API Online",
        "version": "2.1.0",
        "status": "OK",
        "documentation": "/docs",
        "security": "Enhanced"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint (sin autenticación)"""
    return {
        "status": "OK",
        "service": "EstherVital API",
        "version": "2.1.0"
    }


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    debug_mode = os.getenv("DEBUG_MODE", "false").lower() == "true"

    if debug_mode:
        return JSONResponse(
            status_code=422,
            content={
                "detail": "Validation error",
                "errors": exc.errors()
            }
        )
    else:
        return JSONResponse(
            status_code=422,
            content={
                "detail": "Validation error",
                "message": "Los datos proporcionados no son válidos"
            }
        )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled error: {exc}", exc_info=True)

    debug_mode = os.getenv("DEBUG_MODE", "false").lower() == "true"

    if debug_mode:
        return JSONResponse(
            status_code=500,
            content={"detail": str(exc)}
        )
    else:
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )


@app.on_event("startup")
async def startup_event():
    logger.info("✅ EstherVital API starting with enhanced security...")

    required_vars = ["DATABASE_URL", "JWT_SECRET"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        logger.error(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("⚠️  Application may not work correctly!")
    else:
        logger.info("✅ All required environment variables present")

    if os.getenv("DEBUG_MODE", "false").lower() == "true":
        logger.warning("⚠️  DEBUG_MODE is enabled - disable in production!")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("EstherVital API shutting down...")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )