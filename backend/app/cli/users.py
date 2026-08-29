import sys
import uuid
import asyncio
import click
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.cli.utils import (
    print_header,
    print_table,
    print_success,
    print_error,
    print_warning,
    print_info,
)
from app.core.security import get_password_hash


@click.group("users")
def users_group():
    """Emergency user management and credential administration."""
    pass


@users_group.command("list")
@click.option("--department", help="Filter by department name")
def list_users(department):
    """List all registered platform users, roles, and account statuses."""
    print_header("DWRMS USER ACCOUNTS & PRIVILEGES")

    async def _fetch():
        from app.db.session import SessionLocal
        from app.modules.iam.models import User, Department, UserRole, Role

        async with SessionLocal() as session:
            stmt = (
                select(User)
                .options(
                    selectinload(User.department),
                    selectinload(User.roles).selectinload(UserRole.role),
                )
                .order_by(User.email)
            )
            result = await session.execute(stmt)
            users = result.scalars().all()
            
            rows = []
            for u in users:
                dept_name = u.department.name if u.department else "-"
                if department and department.lower() not in dept_name.lower():
                    continue

                role_names = ", ".join(ur.role.name for ur in u.roles if ur.role) or "No Roles"
                status_str = "ACTIVE" if u.is_active else "DISABLED"
                admin_str = "SUPERUSER" if u.is_superuser else "User"

                rows.append([
                    str(u.id)[:8] + "...",
                    u.email,
                    f"{u.first_name} {u.last_name}",
                    dept_name,
                    role_names,
                    status_str,
                    admin_str,
                ])
            return rows

    try:
        rows = asyncio.run(_fetch())
        print_table(["User ID", "Email Address", "Full Name", "Department", "Assigned Roles", "Status", "Privilege"], rows)
        click.echo("")
    except Exception as e:
        print_error(f"Failed to fetch user accounts: {e}")


@users_group.command("create-admin")
@click.option("--email", prompt="Administrator Email", help="Admin email address")
@click.option("--first-name", prompt="First Name", default="System", help="First name")
@click.option("--last-name", prompt="Last Name", default="Administrator", help="Last name")
@click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True, help="Password")
@click.option("--department", default="Maintenance", help="Department name")
def create_admin(email, first_name, last_name, password, department):
    """Create a new authoritative System Administrator account."""
    async def _create():
        from app.db.session import SessionLocal
        from app.modules.iam.models import User, Department, Role, UserRole

        async with SessionLocal() as session:
            # Check existing
            res = await session.execute(select(User).where(User.email == email))
            if res.scalar_one_or_none():
                print_error(f"User with email '{email}' already exists.")
                return False

            res_dept = await session.execute(select(Department).where(Department.name == department))
            dept = res_dept.scalar_one_or_none()
            if not dept:
                dept = Department(name=department, description=f"{department} Department")
                session.add(dept)
                await session.commit()
                await session.refresh(dept)

            res_role = await session.execute(select(Role).where(Role.name == "System Administrator"))
            admin_role = res_role.scalar_one_or_none()

            new_user = User(
                email=email,
                first_name=first_name,
                last_name=last_name,
                hashed_password=get_password_hash(password),
                department_id=dept.id,
                is_active=True,
                is_superuser=True,
            )
            session.add(new_user)
            await session.commit()
            await session.refresh(new_user)

            if admin_role:
                session.add(UserRole(user_id=new_user.id, role_id=admin_role.id))
                await session.commit()
            return True

    try:
        success = asyncio.run(_create())
        if success:
            print_success(f"System Administrator '{email}' created successfully.")
    except Exception as e:
        print_error(f"Error creating admin user: {e}")


@users_group.command("reset-password")
@click.argument("email_or_id")
@click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True, help="New password")
def reset_password(email_or_id, password):
    """Emergency reset of a user's password."""
    async def _reset():
        from app.db.session import SessionLocal
        from app.modules.iam.models import User

        async with SessionLocal() as session:
            # Try UUID or email
            try:
                user_uuid = uuid.UUID(email_or_id)
                stmt = select(User).where(User.id == user_uuid)
            except ValueError:
                stmt = select(User).where(User.email == email_or_id)

            res = await session.execute(stmt)
            user = res.scalar_one_or_none()
            if not user:
                print_error(f"User '{email_or_id}' not found.")
                return False

            user.hashed_password = get_password_hash(password)
            await session.commit()
            return user.email

    try:
        email = asyncio.run(_reset())
        if email:
            print_success(f"Password reset successfully for: {email}")
    except Exception as e:
        print_error(f"Failed to reset password: {e}")


@users_group.command("activate")
@click.argument("email_or_id")
def activate_user(email_or_id):
    """Activate a disabled or locked user account."""
    _set_user_status(email_or_id, active=True)


@users_group.command("deactivate")
@click.argument("email_or_id")
def deactivate_user(email_or_id):
    """Emergency deactivation of a user account."""
    _set_user_status(email_or_id, active=False)


def _set_user_status(email_or_id: str, active: bool):
    action_name = "Activated" if active else "Deactivated"

    async def _run():
        from app.db.session import SessionLocal
        from app.modules.iam.models import User

        async with SessionLocal() as session:
            try:
                user_uuid = uuid.UUID(email_or_id)
                stmt = select(User).where(User.id == user_uuid)
            except ValueError:
                stmt = select(User).where(User.email == email_or_id)

            res = await session.execute(stmt)
            user = res.scalar_one_or_none()
            if not user:
                print_error(f"User '{email_or_id}' not found.")
                return False

            user.is_active = active
            await session.commit()
            return user.email

    try:
        email = asyncio.run(_run())
        if email:
            print_success(f"User {email} has been {action_name.lower()}.")
    except Exception as e:
        print_error(f"Failed to change user status: {e}")
