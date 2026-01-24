from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from jwt import PyJWKClient
import os

security = HTTPBearer()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
# Assuming the user also provides the JWT Secret if we want to verify signature locally 
# or we use the JWKS endpoint (Supabase doesn't expose standard JWKS easily for Auth without custom setup sometimes, 
# but usually it uses HS256 with the JWT Secret). 
# For now, we will verify using the SUPABASE_JWT_SECRET if available, otherwise we might trust the gateway if configured.
# Actually, the best way for Python + Supabase is verifying the JWT signature using the PROJECT_REF and verify with the secret.

# User didn't provide JWT Secret explicitly, but usually it IS the ANON_KEY or separate. 
# Wait, Anon key is a public key effectively for clients. We need the SERVICE_ROLE_KEY or JWT_SECRET to verify tokens?
# Actually, to verify a user's access token, we need the JWT Secret. 
# Let's assume for this step we will extract the payload insecurely OR ask user for JWT Secret if verification fails.
# Correction: Supabase Auth uses HS256 signed with the project's JWT Secret. 
# The user provided ANON_KEY and URL. We need JWT_SECRET to verify signature properly.
# For now, I will create a placeholder validation that checks the "aud" claim matches "authenticated".

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        # PENDING: We need the JWT_SECRET to verify signature. 
        # Ideally: valid_payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"], audience="authenticated")
        
        # Temporary: Decode without verification to get subject (User ID)
        # This is strictly for development until we get the secret.
        payload = jwt.decode(token, options={"verify_signature": False})
        
        if payload.get("aud") != "authenticated":
             raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid audience",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        return payload
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
