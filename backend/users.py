"""
User Management - File-based JSON storage (no database)
"""
import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List
from config import USERS_DIR
from auth import PasswordHandler


class UserManager:
    """Gestiune useri - salvare/citire din JSON files"""

    @staticmethod
    def user_file_path(user_id: str) -> Path:
        """Genereaza cale fișier user"""
        return USERS_DIR / user_id / "profile.json"

    @staticmethod
    def matches_dir(user_id: str) -> Path:
        """Directorul cu predicții user"""
        return USERS_DIR / user_id / "matches"

    @staticmethod
    def create_user(email: str, password: str, full_name: str) -> Dict:
        """
        Creaza user nou

        Returns:
            {
                "status": "success" | "error",
                "user_id": "user_001" | None,
                "message": "User created" | error_msg
            }
        """
        # Verifica daca email deja exista
        existing_user = UserManager.get_user_by_email(email)
        if existing_user:
            return {
                "status": "error",
                "message": "Email already registered"
            }

        # Genereaza user_id unic
        user_id = f"user_{uuid.uuid4().hex[:8]}"
        user_dir = USERS_DIR / user_id

        # Creiaza directoare
        user_dir.mkdir(parents=True, exist_ok=True)
        (UserManager.matches_dir(user_id)).mkdir(parents=True, exist_ok=True)

        # Salveaza user profile
        user_data = {
            "user_id": user_id,
            "email": email,
            "password_hash": PasswordHandler.hash_password(password),
            "full_name": full_name,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "is_active": True,
            "total_predictions": 0
        }

        try:
            with open(UserManager.user_file_path(user_id), 'w') as f:
                json.dump(user_data, f, indent=2)

            return {
                "status": "success",
                "user_id": user_id,
                "message": f"User {email} created successfully"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to create user: {str(e)}"
            }

    @staticmethod
    def get_user_by_email(email: str) -> Optional[Dict]:
        """Cauta user dupa email"""
        for user_dir in USERS_DIR.iterdir():
            if user_dir.is_dir():
                user_file = user_dir / "profile.json"
                if user_file.exists():
                    try:
                        with open(user_file, 'r') as f:
                            user_data = json.load(f)
                            if user_data.get("email") == email:
                                return user_data
                    except:
                        pass
        return None

    @staticmethod
    def get_user_by_id(user_id: str) -> Optional[Dict]:
        """Cauta user dupa ID"""
        user_file = UserManager.user_file_path(user_id)
        if user_file.exists():
            try:
                with open(user_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return None

    @staticmethod
    def get_user_profile(user_id: str) -> Optional[Dict]:
        """Returneaza profile user (fara password)"""
        user = UserManager.get_user_by_id(user_id)
        if not user:
            return None

        user_profile = {
            "user_id": user.get("user_id"),
            "email": user.get("email"),
            "full_name": user.get("full_name"),
            "created_at": user.get("created_at"),
            "total_predictions": user.get("total_predictions", 0)
        }
        return user_profile

    @staticmethod
    def update_prediction_count(user_id: str, increment: int = 1):
        """Incrementeaza contorul de predicții"""
        user_file = UserManager.user_file_path(user_id)
        if user_file.exists():
            try:
                with open(user_file, 'r') as f:
                    user_data = json.load(f)

                user_data["total_predictions"] = user_data.get(
                    "total_predictions", 0) + increment
                user_data["updated_at"] = datetime.utcnow().isoformat()

                with open(user_file, 'w') as f:
                    json.dump(user_data, f, indent=2)

                return True
            except:
                return False
        return False

    @staticmethod
    def verify_credentials(email: str, password: str) -> Optional[str]:
        """
        Verifica email/password

        Returns:
            user_id daca valid, None daca nu
        """
        user = UserManager.get_user_by_email(email)
        if not user:
            return None

        if PasswordHandler.verify_password(password, user.get("password_hash", "")):
            return user.get("user_id")

        return None

    @staticmethod
    def list_all_users() -> List[Dict]:
        """Listeaza toti userii (admin endpoint)"""
        users = []
        for user_dir in USERS_DIR.iterdir():
            if user_dir.is_dir():
                user_file = user_dir / "profile.json"
                if user_file.exists():
                    try:
                        with open(user_file, 'r') as f:
                            user_data = json.load(f)
                            # Elimina password
                            user_data.pop("password_hash", None)
                            users.append(user_data)
                    except:
                        pass
        return users
