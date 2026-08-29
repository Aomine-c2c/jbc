import abc
from typing import Optional
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.modules.iam.models import User
from app.core.security import verify_password
from app.core.config import settings

class AuthenticationProvider(abc.ABC):
    """Abstract base class for authentication providers (Local DB, LDAP, AD)."""

    @abc.abstractmethod
    async def authenticate(self, db: AsyncSession, username: str, password: str) -> Optional[User]:
        pass

class LocalDatabaseAuthProvider(AuthenticationProvider):
    """Authenticates users against the local DWRMS SQLite/MySQL database."""
    
    async def authenticate(self, db: AsyncSession, username: str, password: str) -> Optional[User]:
        result = await db.execute(select(User).where(User.email == username))
        user = result.scalar_one_or_none()
        
        if not user:
            return None
            
        if not verify_password(password, user.hashed_password):
            return None
            
        return user

class LDAPAuthProvider(AuthenticationProvider):
    """LDAP/AD integration with auto-provisioning."""
    
    async def authenticate(self, db: AsyncSession, username: str, password: str) -> Optional[User]:
        import ldap3
        
        # 1. Bind to LDAP server
        if not settings.LDAP_SERVER_URL:
            return None
            
        server = ldap3.Server(settings.LDAP_SERVER_URL, get_info=ldap3.ALL)
        
        # Try direct bind with user provided credentials if no bind DN is configured
        # Or construct UPN if domain is known, but usually user inputs email or domain\\user
        # We will attempt to connect and bind using the user's input as the bind DN/UPN
        bind_user = username
        if settings.LDAP_BIND_DN and settings.LDAP_BIND_PASSWORD:
            # Service account bind to search for the user first
            conn = ldap3.Connection(server, user=settings.LDAP_BIND_DN, password=settings.LDAP_BIND_PASSWORD, auto_bind=True)
            search_filter = f"(&(objectClass=user)(|(sAMAccountName={username})(userPrincipalName={username})(mail={username})))"
            conn.search(settings.LDAP_USER_BASE_DN or "", search_filter, attributes=['cn', 'mail', 'givenName', 'sn', 'distinguishedName'])
            
            if not conn.entries:
                return None
                
            entry = conn.entries[0]
            bind_user = entry.entry_dn
            
            # Now bind as the user to verify password
            user_conn = ldap3.Connection(server, user=bind_user, password=password)
            if not user_conn.bind():
                return None
                
            email = str(entry.mail) if 'mail' in entry else username
            first_name = str(entry.givenName) if 'givenName' in entry else "LDAP"
            last_name = str(entry.sn) if 'sn' in entry else "User"
            
        else:
            # Direct bind attempt
            conn = ldap3.Connection(server, user=bind_user, password=password)
            if not conn.bind():
                return None
                
            email = username
            first_name = "LDAP"
            last_name = "User"
            
        # 3. Lookup user in local DWRMS db by email
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        
        # 4. If user does not exist, auto-provision User object
        if not user:
            user = User(
                email=email,
                first_name=first_name,
                last_name=last_name,
                hashed_password="[LDAP_MANAGED]",  # Password not stored locally
                department_id=None,
                is_active=True
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            
        return user

def get_auth_provider() -> AuthenticationProvider:
    """Factory to return the active authentication provider based on environment config."""
    if settings.AUTH_METHOD == "LDAP":
        return LDAPAuthProvider()
    return LocalDatabaseAuthProvider()
