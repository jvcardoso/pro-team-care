"""
Pure Domain Entities - Clean Architecture
Entidades de negócio puras, sem dependências de frameworks
"""
from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class User:
    """
    Entidade User pura de domínio
    Representa um usuário do sistema sem dependências de frameworks
    """
    id: int
    person_id: int
    email_address: str
    is_active: bool
    is_system_admin: bool
    created_at: datetime
    updated_at: datetime
    
    # Campos opcionais
    email_verified_at: Optional[datetime] = None
    remember_token: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None
    notification_settings: Optional[Dict[str, Any]] = None
    two_factor_secret: Optional[str] = None
    two_factor_recovery_codes: Optional[str] = None
    last_login_at: Optional[datetime] = None
    password_changed_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    
    def is_verified(self) -> bool:
        """Check if user email is verified"""
        return self.email_verified_at is not None
    
    def is_admin(self) -> bool:
        """Check if user is system admin"""
        return self.is_system_admin
    
    def has_two_factor(self) -> bool:
        """Check if user has 2FA enabled"""
        return self.two_factor_secret is not None
    
    def can_login(self) -> bool:
        """Check if user can login (active and verified)"""
        return self.is_active and self.is_verified()
    
    def update_last_login(self, login_time: datetime) -> None:
        """Update last login timestamp"""
        self.last_login_at = login_time
        self.updated_at = datetime.utcnow()
    
    def activate(self) -> None:
        """Activate user account"""
        self.is_active = True
        self.updated_at = datetime.utcnow()
    
    def deactivate(self) -> None:
        """Deactivate user account"""
        self.is_active = False
        self.updated_at = datetime.utcnow()