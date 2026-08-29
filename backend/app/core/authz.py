from fastapi import HTTPException, status
from typing import Dict, List, Any
from app.modules.iam.models import User, Scope
import uuid

class AuthzGuard:
    """Central authorization guard for DWRMS."""

    @staticmethod
    def check_permission(
        user: User,
        permission: str,
        user_permissions: Dict[str, List[Any]],
        resource_owner_id: uuid.UUID | None = None,
        resource_dept_id: uuid.UUID | None = None,
        assigned_user_id: uuid.UUID | None = None,
    ) -> bool:
        """Check if user has required permission for the given context."""
        
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
        if "GLOBAL" in scope_names or not scope_names:
            return True

        # Check DEPARTMENT scope
        if "DEPARTMENT" in scope_names:
            if not resource_dept_id:
                return True
            if user.department_id and str(user.department_id) == str(resource_dept_id):
                return True
        
        # Check ASSIGNED scope
        if "ASSIGNED" in scope_names:
            if assigned_user_id and str(user.id) == str(assigned_user_id):
                return True

        # Check OWN scope
        if "OWN" in scope_names:
            if not resource_owner_id:
                return True
            if str(user.id) == str(resource_owner_id):
                return True

        return False
