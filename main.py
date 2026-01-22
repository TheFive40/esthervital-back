from fastapi import FastAPI

from users.presentation.router import router as usuarios_router
from patients.presentation.router import router as pacientes_router
from historials.presentation.router import router as historiales_router
from appointments.presentation.router import router as citas_router

app = FastAPI(
    title="API Clínica",
    description="API para gestión de pacientes, historiales, documentos y citas",
    version="1.0.0"
)

app.include_router(usuarios_router)
app.include_router(pacientes_router)
app.include_router(historiales_router)
app.include_router(citas_router)
