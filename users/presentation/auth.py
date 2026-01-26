from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from shared.database import get_db
from users.infrastructure.repositories import UsuarioRepository
from security.hashing import Hash
from security.token import create_access_token

auth_router = APIRouter(
    prefix="/auth",
    tags=["Autenticación"]
)

@auth_router.post("/login")
def login(request: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    repo = UsuarioRepository(db)
    
    # 1. Buscamos al usuario por email
    # OJO: Swagger envía el email en el campo 'username'
    usuario = repo.get_by_email(request.username)
    
    # 2. Si no existe, error
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credenciales inválidas"
        )
    
    # 3. Verificamos si la contraseña coincide
    if not Hash.verify(request.password, usuario.password):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contraseña incorrecta"
        )

    # 4. Si todo está bien, creamos el Token
    access_token = create_access_token(data={"sub": usuario.email})
    
    return {"access_token": access_token, "token_type": "bearer"}