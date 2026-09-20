#!/usr/bin/env bash
# ==============================================================================
# BIKITA MINERALS DWRMS — Login Diagnostic & Self-Repair Tool (Linux/macOS)
# Run from the project root to diagnose and fix login failures.
# Usage: ./fix-login.sh
# ==============================================================================

set -uo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="${SCRIPT_DIR}/backend"
ENV_FILE="${SCRIPT_DIR}/.env"
VENV_PYTHON="${BACKEND_DIR}/.venv/bin/python"

echo -e "${CYAN}${BOLD}======================================================================"
echo -e "   DWRMS Login Diagnostic & Self-Repair Tool"
echo -e "   Run from the project root directory."
echo -e "======================================================================${NC}"
echo ""

# ── Step 1: Python ────────────────────────────────────────────────────────────
echo -e "${BOLD}[1/6] Checking Python availability...${NC}"
if command -v python3 >/dev/null 2>&1; then
    PY=python3
elif command -v python >/dev/null 2>&1; then
    PY=python
else
    echo -e "${RED}[FAIL] Python not found. Install Python 3.10+ first.${NC}"
    exit 1
fi
echo -e "${GREEN}[OK] Python found: $(${PY} --version)${NC}"

# ── Step 2: .env file ─────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}[2/6] Checking .env configuration file...${NC}"
if [[ ! -f "$ENV_FILE" ]]; then
    echo -e "${RED}[FAIL] .env not found!${NC}"
    if [[ -f "${SCRIPT_DIR}/.env.example" ]]; then
        echo -e "${YELLOW}[FIX] Creating .env from .env.example...${NC}"
        cp "${SCRIPT_DIR}/.env.example" "$ENV_FILE"
        echo -e "${GREEN}[OK] .env created.${NC}"
    else
        echo -e "${RED}[FAIL] .env.example also not found. Re-clone the repository.${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}[OK] .env file exists.${NC}"
fi

# ── Step 3: ENVIRONMENT setting ───────────────────────────────────────────────
echo ""
echo -e "${BOLD}[3/6] Checking ENVIRONMENT setting...${NC}"
env_val=$(grep -E '^ENVIRONMENT=' "$ENV_FILE" | head -1 | cut -d'=' -f2 | tr -d '"' | tr -d "'" | tr -d '[:space:]' || true)
if [[ "$env_val" == "production" ]]; then
    echo -e "${RED}[FAIL] ENVIRONMENT=production!${NC}"
    echo ""
    echo -e "${RED}  ROOT CAUSE FOUND: This is why you cannot login.${NC}"
    echo -e "${YELLOW}  When ENVIRONMENT=production, the demo password fallback is DISABLED."
    echo -e "  Users with password 'password123' cannot authenticate in production mode.${NC}"
    echo ""
    echo -e "${YELLOW}[FIX] Changing ENVIRONMENT to 'testing'...${NC}"
    sed -i 's/^ENVIRONMENT=.*/ENVIRONMENT="testing"/' "$ENV_FILE"
    echo -e "${GREEN}[OK] ENVIRONMENT changed to 'testing'.${NC}"
elif [[ -z "$env_val" ]]; then
    echo -e "${YELLOW}[WARN] ENVIRONMENT not set. Adding ENVIRONMENT=\"testing\"...${NC}"
    echo 'ENVIRONMENT="testing"' >> "$ENV_FILE"
    echo -e "${GREEN}[OK] ENVIRONMENT set.${NC}"
else
    echo -e "${GREEN}[OK] ENVIRONMENT = ${env_val} (compatible with demo logins)${NC}"
fi

# ── Step 4: SECRET_KEY ────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}[4/6] Checking SECRET_KEY...${NC}"
secret_val=$(grep -E '^SECRET_KEY=' "$ENV_FILE" | head -1 | cut -d'=' -f2 | tr -d '"' | tr -d "'" | tr -d '[:space:]' || true)
if [[ -z "$secret_val" ]] || [[ "$secret_val" == "dev-changeme-please-set-a-real-secret-in-production" ]]; then
    echo -e "${YELLOW}[WARN] SECRET_KEY is empty/placeholder. Generating one...${NC}"
    new_secret=$($PY -c "import secrets; print(secrets.token_hex(32))")
    if grep -qE '^SECRET_KEY=' "$ENV_FILE"; then
        sed -i "s|^SECRET_KEY=.*|SECRET_KEY=\"${new_secret}\"|" "$ENV_FILE"
    else
        echo "SECRET_KEY=\"${new_secret}\"" >> "$ENV_FILE"
    fi
    echo -e "${GREEN}[OK] SECRET_KEY generated and saved.${NC}"
else
    echo -e "${GREEN}[OK] SECRET_KEY is set.${NC}"
fi

# ── Step 5: Database & Users ──────────────────────────────────────────────────
echo ""
echo -e "${BOLD}[5/6] Checking database and user accounts...${NC}"
if [[ ! -f "$VENV_PYTHON" ]]; then
    echo -e "${YELLOW}[WARN] Python virtualenv not found. Run './run.sh deps' first.${NC}"
else
    (
        cd "$BACKEND_DIR"
        "$VENV_PYTHON" - <<'PYEOF'
import asyncio, sys
sys.path.insert(0, '.')

async def check():
    from app.db.session import async_session_factory
    from app.modules.iam.models import User
    from sqlalchemy import select
    from app.core.security import verify_password

    async with async_session_factory() as db:
        users = (await db.execute(select(User))).scalars().all()
        if not users:
            print('[FAIL] No users in database! Run: ./run.sh deps')
            return
        print(f'[OK] Found {len(users)} users in database.')
        for u in users:
            pw_ok = verify_password('password123', u.hashed_password)
            dept_ok = bool(u.department_id)
            active = u.is_active
            status = 'OK' if (pw_ok and dept_ok and active) else 'ISSUE'
            print(f'  [{status}] {u.email}: password={pw_ok} | active={active} | has_dept={dept_ok}')
            if not pw_ok:
                print(f'    ^ Password mismatch — user may need re-seeding or was manually created')
            if not dept_ok:
                print(f'    ^ No department — login returns 403 Account pending approval')
            if not active:
                print(f'    ^ User is disabled — login returns 403 User is disabled')

asyncio.run(check())
PYEOF
    )
fi

# ── Step 6: Quick login test ──────────────────────────────────────────────────
echo ""
echo -e "${BOLD}[6/6] Quick login test (requires backend running at :8000)...${NC}"
if command -v curl >/dev/null 2>&1; then
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
        -X POST "http://127.0.0.1:8000/api/v1/iam/auth/login" \
        -H "Content-Type: application/json" \
        -d '{"username":"admin@bikita.com","password":"password123"}' \
        --connect-timeout 3 2>/dev/null || echo "000")
    if [[ "$HTTP_CODE" == "200" ]]; then
        echo -e "${GREEN}[OK] Login SUCCESSFUL! Backend authenticated correctly.${NC}"
    elif [[ "$HTTP_CODE" == "400" ]]; then
        echo -e "${RED}[FAIL] HTTP 400 — Incorrect email or password.${NC}"
        echo -e "${YELLOW}  Possible causes: ENVIRONMENT not 'testing/development', or database not seeded.${NC}"
        echo -e "${YELLOW}  Restart backend after changes above, then try: ./run.sh deps${NC}"
    elif [[ "$HTTP_CODE" == "403" ]]; then
        echo -e "${RED}[FAIL] HTTP 403 — Account blocked (inactive or no department).${NC}"
        echo -e "${YELLOW}  Run: ./run.sh deps to reseed the database.${NC}"
    elif [[ "$HTTP_CODE" == "000" ]]; then
        echo -e "${YELLOW}[SKIP] Backend not running. Start it first with: ./run.sh all${NC}"
    else
        echo -e "${YELLOW}[WARN] Unexpected HTTP ${HTTP_CODE} from backend.${NC}"
    fi
else
    echo -e "${YELLOW}[SKIP] curl not found. Skipping live login test.${NC}"
fi

echo ""
echo -e "${CYAN}${BOLD}======================================================================"
echo -e " Diagnosis complete."
echo -e " If issues were auto-fixed, restart the stack: ./run.sh all"
echo -e " If database had no users, reseed first: ./run.sh deps"
echo -e "======================================================================${NC}"
