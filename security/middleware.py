"""
Security Middleware - Authentication, Role-based Authorization, and Replay Protection
"""
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Set
import os
from enum import Enum
import hashlib

# Security configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

security = HTTPBearer(auto_error=False)

class UserRole(str, Enum):
    GOVERNOR = "Governor"
    REVIEWER = "Reviewer"
    OPERATOR = "Operator"
    READONLY = "Read Only"

# Memory store for spent signature tokens / replay validation
USED_APPROVAL_TOKENS: Set[str] = set()

def register_used_approval_token(token: str) -> None:
    """Track approval token to prevent replay attacks (persistent and process-local cache)"""
    if not token:
        return
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    
    # 1. Process-local cache check
    if token_hash in USED_APPROVAL_TOKENS:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="REPLAY_REJECT: This approval token or signature has already been processed."
        )
        
    # 2. Database persistent check
    try:
        from db.db_config import session_factory
        from db.models import SpentTokenModel
        
        db = session_factory()
        try:
            exists = db.query(SpentTokenModel).filter(SpentTokenModel.token_hash == token_hash).first()
            if exists:
                USED_APPROVAL_TOKENS.add(token_hash)
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="REPLAY_REJECT: This approval token or signature has already been processed."
                )
            
            new_token = SpentTokenModel(token_hash=token_hash)
            db.add(new_token)
            db.commit()
            USED_APPROVAL_TOKENS.add(token_hash)
        except HTTPException:
            raise
        except Exception as e:
            import logging
            logging.getLogger("security").error(f"DB Error in register_used_approval_token: {e}", exc_info=True)
            db.rollback()
            # Robustness fallback to memory cache if DB throws/locks
            USED_APPROVAL_TOKENS.add(token_hash)
        finally:
            db.close()
    except HTTPException:
        raise
    except Exception:
        # Fallback to local memory cache if database module loading fails
        USED_APPROVAL_TOKENS.add(token_hash)


class SecurityConfig:
    """Security configuration and utilities"""
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
        """Create JWT access token"""
        to_encode = data.copy()
        now = datetime.now(timezone.utc)
        if expires_delta:
            expire = now + expires_delta
        else:
            expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": int(expire.timestamp())})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
        """Verify JWT token and enforce expiration"""
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )
        try:
            payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            role: str = payload.get("role")
            exp: int = payload.get("exp")
            
            if username is None or role is None or exp is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Expired credential validation
            now = datetime.now(timezone.utc).timestamp()
            if now > exp:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Expired credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            return {"username": username, "role": role}
            
        except JWTError as e:
            detail = f"Invalid token: {str(e)}"
            if "expired" in str(e).lower():
                detail = "Expired credentials"
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=detail, 
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    @staticmethod
    def require_roles(allowed_roles: List[UserRole]):
        """Decorator to require specific roles"""
        def role_checker(current_user: dict = Depends(SecurityConfig.verify_token)):
            if current_user["role"] not in [r.value for r in allowed_roles]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions. Requires roles: {[r.value for r in allowed_roles]}"
                )
            return current_user
        return role_checker

# Authentication dependencies
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user"""
    return SecurityConfig.verify_token(credentials)

def require_governor(current_user: dict = Depends(SecurityConfig.require_roles([UserRole.GOVERNOR]))):
    """Require Governor role"""
    return current_user

def require_reviewer_or_governor(current_user: dict = Depends(SecurityConfig.require_roles([UserRole.REVIEWER, UserRole.GOVERNOR]))):
    """Require Reviewer or Governor role"""
    return current_user

def require_operator_or_governor(current_user: dict = Depends(SecurityConfig.require_roles([UserRole.OPERATOR, UserRole.GOVERNOR]))):
    """Require Operator or Governor role"""
    return current_user

def require_any_authenticated(current_user: dict = Depends(SecurityConfig.verify_token)):
    """Require any authenticated role"""
    return current_user

def validate_startup_secrets():
    """Validate runtime secrets on startup — hard exit if insecure."""
    import sys
    secret = os.getenv("JWT_SECRET_KEY")
    insecure_defaults = {
        "your-secret-key-change-in-production",
        "your-super-secret-jwt-key-change-this-in-production-min-32-chars"
    }
    if not secret or secret in insecure_defaults:
        # Allow override in local dev only
        if os.getenv("ALLOW_INSECURE_JWT", "").lower() == "true":
            import logging
            logging.getLogger("security").warning(
                "SECURITY WARNING: Insecure JWT_SECRET_KEY — allowed by ALLOW_INSECURE_JWT=true"
            )
            return
        sys.exit(
            "FATAL: Insecure or default JWT_SECRET_KEY detected. "
            "Set a strong JWT_SECRET_KEY environment variable before starting the server. "
            "Set ALLOW_INSECURE_JWT=true to bypass in local development only."
        )