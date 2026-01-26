from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging

from users.presentation.router import router as usuarios_router
from patients.presentation.router import router as pacientes_router
from historials.presentation.router import router as historiales_router
from appointments.presentation.router import router as citas_router
from treatments.presentation.router import router as tratamientos_router

from shared.database import Base, engine
from shared.middleware import (
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
    RequestLoggingMiddleware
)
from shared.auth_router import router as auth_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="API EstherVital",
    description="API para gestion de pacientes, historiales, citas y tratamientos",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

Base.metadata.create_all(bind=engine)

app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "https://esthervital-front.vercel.app",
    "https://esthervital-staging.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(usuarios_router)
app.include_router(pacientes_router)
app.include_router(historiales_router)
app.include_router(citas_router)
app.include_router(tratamientos_router)


@app.get("/")
async def root():
    return {
        "message": "EstherVital API Online",
        "version": "2.0.0",
        "status": "OK",
        "documentation": "/docs"
    }


@app.get("/health")
async def health_check():
    return {
        "status": "OK",
        "service": "EstherVital API"
    }


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Validation error",
            "errors": exc.errors()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


@app.on_event("startup")
async def startup_event():
    logger.info("EstherVital API starting...")


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