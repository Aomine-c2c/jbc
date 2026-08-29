from fastapi import HTTPException, status
from typing import Dict, List, Any
from app.modules.iam.models import User, Scope
import uuid

class AuthzGuard:
    """Central authorization guard for DWRMS."""

    @staticmethod
    def get_user_permissions(user: User) -> dict[str, list[Scope]]:
        """Collect all permission names mapped to scopes granted to a user through their roles."""
        perms = {}
        try:
            for ur in (user.roles or []):
                if getattr(ur, "role", None):
                    for rp in (ur.role.role_permissions or []):
                        if getattr(rp, "permission", None):
                            perm_name = rp.permission.name
                            if perm_name not in perms:
                                perms[perm_name] = []
                            if getattr(rp, "scope", None):
                                perms[perm_name].append(rp.scope)
        except Exception:
            pass
        if getattr(user, "is_superuser", False):
            perms["global_override"] = []
        mock_perms = getattr(user, "mock_permissions", None)
        if mock_perms:
            for p in mock_perms:
                if p not in perms:
                    perms[p] = []
        return perms

    @staticmethod
    def check_permission(
        user: User,
        permission: str,
        user_permissions: Dict[str, List[Any]] | None = None,
        resource_owner_id: uuid.UUID | None = None,
        resource_dept_id: uuid.UUID | None = None,
        assigned_user_id: uuid.UUID | None = None,
    ) -> bool:
        """Check if user has required permission for the given context."""
        if user_permissions is None:
            user_permissions = AuthzGuard.get_user_permissions(user)
        
        # Self-approval check constraint
        if permission.endswith(":approve") and resource_owner_id and user.id == resource_owner_id:
            raise HTTPException(
                status_code=409,
                detail="Separation of Duties violation: cannot approve your own request"
            )

        if "global_override" in user_permissions:
            return True

        scopes_raw = user_permissions.get(permission, [])
        if not scopes_raw:
            return False

        # Normalize scopes to string names
        scope_names = set()
        for s in scopes_raw:
            if isinstance(s, Scope):
                scope_names.add(s.value.upper())
                scope_names.add(s.name.upper())
            elif isinstance(s, str):
                scope_names.add(s.upper())

        # If user has GLOBAL scope for this permission, allow
        if "GLOBAL" in scope_names:
            return True

        # Check DEPARTMENT scope
        if "DEPARTMENT" in scope_names:
            if resource_dept_id and user.department_id and str(user.department_id) == str(resource_dept_id):
                return True
        
        # Check ASSIGNED scope
        if "ASSIGNED" in scope_names:
            if assigned_user_id and str(user.id) == str(assigned_user_id):
                return True

        # Check OWN scope
        if "OWN" in scope_names:
            if resource_owner_id and str(user.id) == str(resource_owner_id):
                return True

        return False
