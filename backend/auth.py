import streamlit as st
import hashlib
import json
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

class UserRole(Enum):
    ADMIN = "admin"
    USER = "user"

@dataclass
class User:
    username: str
    email: str
    role: UserRole
    created_at: str
    last_login: Optional[str] = None
    is_active: bool = True

class AuthManager:
    def __init__(self):
        self.users_file = Path("app/data/users.json")
        self.users_file.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_default_users()
    
    def _ensure_default_users(self):
        """Create default users if they don't exist"""
        if not self.users_file.exists():
            default_users = {
                "admin": {
                    "username": "admin",
                    "email": "admin@metrology.com",
                    "password_hash": self._hash_password("admin123"),
                    "role": UserRole.ADMIN.value,
                    "created_at": "2024-01-01",
                    "is_active": True
                },
                "user": {
                    "username": "user",
                    "email": "user@metrology.com", 
                    "password_hash": self._hash_password("user123"),
                    "role": UserRole.USER.value,
                    "created_at": "2024-01-01",
                    "is_active": True
                }
            }
            self.users_file.write_text(json.dumps(default_users, indent=2))
    
    def _hash_password(self, password: str) -> str:
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _load_users(self) -> Dict[str, Dict[str, Any]]:
        """Load users from file"""
        try:
            return json.loads(self.users_file.read_text())
        except:
            return {}
    
    def _save_users(self, users: Dict[str, Dict[str, Any]]):
        """Save users to file"""
        self.users_file.write_text(json.dumps(users, indent=2))
    
    def authenticate(self, username: str, password: str) -> Optional[User]:
        """Authenticate user with username and password"""
        users = self._load_users()
        
        if username not in users:
            return None
        
        user_data = users[username]
        if not user_data.get("is_active", True):
            return None
        
        password_hash = self._hash_password(password)
        if user_data["password_hash"] != password_hash:
            return None
        
        # Update last login
        user_data["last_login"] = pd.Timestamp.now().isoformat()
        self._save_users(users)
        
        return User(
            username=user_data["username"],
            email=user_data["email"],
            role=UserRole(user_data["role"]),
            created_at=user_data["created_at"],
            last_login=user_data.get("last_login")
        )
    
    def create_user(self, username: str, email: str, password: str, role: UserRole) -> bool:
        """Create a new user"""
        users = self._load_users()
        
        if username in users:
            return False
        
        users[username] = {
            "username": username,
            "email": email,
            "password_hash": self._hash_password(password),
            "role": role.value,
            "created_at": pd.Timestamp.now().isoformat(),
            "is_active": True
        }
        
        self._save_users(users)
        return True
    
    def get_user(self, username: str) -> Optional[User]:
        """Get user by username"""
        users = self._load_users()
        
        if username not in users:
            return None
        
        user_data = users[username]
        return User(
            username=user_data["username"],
            email=user_data["email"],
            role=UserRole(user_data["role"]),
            created_at=user_data["created_at"],
            last_login=user_data.get("last_login"),
            is_active=user_data.get("is_active", True)
        )
    
    def get_all_users(self) -> list[User]:
        """Get all users (admin only)"""
        users = self._load_users()
        return [
            User(
                username=data["username"],
                email=data["email"],
                role=UserRole(data["role"]),
                created_at=data["created_at"],
                last_login=data.get("last_login"),
                is_active=data.get("is_active", True)
            )
            for data in users.values()
        ]
    
    def update_user_status(self, username: str, is_active: bool) -> bool:
        """Update user active status"""
        users = self._load_users()
        
        if username not in users:
            return False
        
        users[username]["is_active"] = is_active
        self._save_users(users)
        return True

def get_current_user() -> Optional[User]:
    """Get current logged in user from session state"""
    return st.session_state.get("user")

def is_authenticated() -> bool:
    """Check if user is authenticated"""
    return "user" in st.session_state and st.session_state.user is not None

def is_admin() -> bool:
    """Check if current user is admin"""
    user = get_current_user()
    return user is not None and user.role == UserRole.ADMIN

def require_auth():
    """Decorator to require authentication for a page"""
    if not is_authenticated():
        st.error("Please log in to access this page.")
        st.stop()

def require_admin():
    """Decorator to require admin access for a page"""
    if not is_authenticated():
        st.error("Please log in to access this page.")
        st.stop()
    
    if not is_admin():
        st.error("Admin access required for this page.")
        st.stop()