from fastapi import FastAPI
from users.presentation.router import router as usuarios_router
app = FastAPI()

app.include_router(usuarios_router)
