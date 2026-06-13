"""
JWT Authentication Logic - Registrare, Login, Token Validation
"""
import jwt
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict
from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES


class JWTHandler:
    """Generare și validare JWT tokens"""

    @staticmethod
    def create_access_token(user_id: str, email: str) -> Dict[str, str]:
        """
        Creiază JWT access token

        Returns:
            {
                "access_token": "token_string",
                "expires_in": 3600,
                "token_type": "bearer"
            }
        """
        payload = {
            "user_id": user_id,
            "email": email,
            "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
            "iat": datetime.utcnow()
        }

        encoded_jwt = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

        return {
            "access_token": encoded_jwt,
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "token_type": "bearer"
        }

    @staticmethod
    def verify_token(token: str) -> Optional[Dict]:
        """
        Verifică validitatea JWT token

        Returns:
            Payload dict dacă valid, None dacă expirat/invalid
        """
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            print("Token expirat")
            return None
        except jwt.InvalidTokenError:
            print("Token invalid")
            return None

    @staticmethod
    def decode_token(token: str) -> Optional[str]:
        """Extrage user_id din token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload.get("user_id")
        except:
            return None


class PasswordHandler:
    """Hashing și verificare parole"""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash o parolă cu SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verifică o parolă plaintext contra hash-ului"""
        return PasswordHandler.hash_password(plain_password) == hashed_password


# === Helper Functions ===

def extract_token_from_header(authorization: str) -> Optional[str]:
    """Extrage token din Authorization header"""
    try:
        # Format: "Bearer token_string"
        parts = authorization.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            return parts[1]
        return None
    except:
        return None
