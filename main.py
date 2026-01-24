from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from users.presentation.router import router as usuarios_router
from patients.presentation.router import router as pacientes_router
from historials.presentation.router import router as historiales_router
from appointments.presentation.router import router as citas_router
from treatments.presentation.router import router as tratamientos_router

from shared.database import Base, engine

app = FastAPI(
    title="API Clínica",
    description="API para gestión de pacientes, historiales, documentos y citas",
    version="1.0.0"
)

# Create tables
Base.metadata.create_all(bind=engine)

# Configure CORS
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://esthervital-front.vercel.app", 
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(usuarios_router)
app.include_router(pacientes_router)
app.include_router(historiales_router)
app.include_router(citas_router)
app.include_router(tratamientos_router)
