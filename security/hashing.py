from passlib.context import CryptContext

# Usamos bcrypt, que es el estándar de oro hoy en día
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class Hash:
    @staticmethod
    def bcrypt(password: str):
        """Convierte 'hola123' en un hash ilegible"""
        return pwd_context.hash(password)

    @staticmethod
    def verify(plain_password, hashed_password):
        """Compara si la contraseña que escribió el usuario coincide con el hash"""
        return pwd_context.verify(plain_password, hashed_password)