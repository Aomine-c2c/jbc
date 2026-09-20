#!/usr/bin/env bash
# ==============================================================================
# BIKITA MINERALS DWRMS — ONE-COMMAND DEVELOPER LAUNCHER
#
# Default: Launches the full Tauri Desktop App in developer mode.
# Automatically installs Rust if missing, runs preflight checks,
# starts FastAPI backend silently, then opens the Tauri native window.
#
# Usage:
#   ./run.sh                  Default: Tauri desktop dev mode (auto-installs Rust)
#   ./run.sh tauri            Same as default
#   ./run.sh web              Full web stack (FastAPI + Next.js in browser)
#   ./run.sh backend          FastAPI backend only
#   ./run.sh frontend         Next.js frontend only
#   ./run.sh deps             Setup/verify all dependencies & init DB
#   ./run.sh help             Show help
# ==============================================================================

set -uo pipefail

# ── Color Palette & Formatting ────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m' # No Color

# ── Paths ─────────────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="${SCRIPT_DIR}/backend"
FRONTEND_DIR="${SCRIPT_DIR}/frontend"
ROOT_ENV="${SCRIPT_DIR}/.env"
ROOT_ENV_EXAMPLE="${SCRIPT_DIR}/.env.example"
FRONTEND_ENV_LOCAL="${FRONTEND_DIR}/.env.local"
VENV_DIR="${BACKEND_DIR}/.venv"
VENV_PYTHON="${VENV_DIR}/bin/python"
VENV_PIP="${VENV_DIR}/bin/pip"
VENV_UVICORN="${VENV_DIR}/bin/uvicorn"

# Track child PIDs for clean termination
CHILD_PIDS=()

log_info() {
    echo -e "${CYAN}[DWRMS]${NC} $1"
}

log_success() {
    echo -e "${GREEN}${BOLD}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}${BOLD}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}${BOLD}[ERROR]${NC} $1"
}

banner() {
    echo -e "${BLUE}${BOLD}======================================================================${NC}"
    echo -e "${BLUE}${BOLD}   BIKITA MINERALS DWRMS — DEVELOPER STACK LAUNCHER                   ${NC}"
    echo -e "${BLUE}${BOLD}   Authoritative Operations & Mining Resource Management               ${NC}"
    echo -e "${BLUE}${BOLD}======================================================================${NC}"
}

# ── Cleanup Handler ───────────────────────────────────────────────────────────
cleanup() {
    # Disable trap during cleanup to prevent recursive signal handling
    trap - INT TERM EXIT

    if [[ ${#CHILD_PIDS[@]} -gt 0 ]]; then
        echo -e "\n${YELLOW}[DWRMS] Shutting down running services gracefully...${NC}"
        for pid in "${CHILD_PIDS[@]}"; do
            if kill -0 "$pid" 2>/dev/null; then
                # Send SIGTERM to process group if supported, else direct PID
                kill -TERM "-$pid" 2>/dev/null || kill -TERM "$pid" 2>/dev/null
            fi
        done
        
        # Brief grace period
        sleep 1

        # Force kill any stubborn processes
        for pid in "${CHILD_PIDS[@]}"; do
            if kill -0 "$pid" 2>/dev/null; then
                kill -KILL "-$pid" 2>/dev/null || kill -KILL "$pid" 2>/dev/null
            fi
        done
        CHILD_PIDS=()
        log_success "All development services stopped."
    fi
    exit 0
}

trap cleanup INT TERM EXIT

# ── Ensure Rust/Cargo is Available (auto-install if missing) ──────────────────
ensure_rust() {
    if command -v cargo >/dev/null 2>&1; then
        log_info "Rust/Cargo: $(cargo --version) (${GREEN}OK${NC})"
        return 0
    fi

    # Also try ~/.cargo/bin in case it was installed but not in PATH yet
    if [[ -x "${HOME}/.cargo/bin/cargo" ]]; then
        export PATH="${HOME}/.cargo/bin:${PATH}"
        log_info "Rust/Cargo found at ~/.cargo/bin (${GREEN}OK${NC})"
        return 0
    fi

    log_warn "Rust/Cargo not found — required for Tauri Desktop mode."
    log_info "Auto-installing Rust via rustup.rs..."

    if ! command -v curl >/dev/null 2>&1; then
        log_error "curl is required to install Rust. Install curl first: sudo apt install curl"
        exit 1
    fi

    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --default-toolchain stable
    if [[ $? -ne 0 ]]; then
        log_error "Rust installation failed. Install manually from https://rustup.rs/"
        exit 1
    fi

    # Source cargo env for this session
    # shellcheck disable=SC1091
    source "${HOME}/.cargo/env" 2>/dev/null || export PATH="${HOME}/.cargo/bin:${PATH}"

    if ! command -v cargo >/dev/null 2>&1; then
        log_error "Rust installed but cargo still not found. Please close and reopen your terminal."
        exit 1
    fi
    log_success "Rust installed: $(cargo --version)"
}

# ── Port Conflict Resolution ──────────────────────────────────────────────────
resolve_port() {
    local port="$1"
    local service_name="$2"
    local pids=""

    # 1. Check with fuser
    if command -v fuser >/dev/null 2>&1; then
        pids=$(fuser "${port}/tcp" 2>/dev/null | tr -s ' ' '\n' | grep -E '^[0-9]+$' || true)
    fi

    # 2. Check with ss if fuser found nothing
    if [[ -z "$pids" ]] && command -v ss >/dev/null 2>&1; then
        pids=$(ss -tulpn "sport = :${port}" 2>/dev/null | grep -oE 'pid=[0-9]+' | cut -d= -f2 | sort -u || true)
    fi

    # 3. Check with lsof if still empty
    if [[ -z "$pids" ]] && command -v lsof >/dev/null 2>&1; then
        pids=$(lsof -ti ":${port}" 2>/dev/null || true)
    fi

    if [[ -n "$pids" ]]; then
        log_warn "Port ${port} (${service_name}) is currently occupied by PID(s): ${pids}."
        log_info "Terminating stale process(es) to ensure clean startup..."
        for p in $pids; do
            kill -15 "$p" 2>/dev/null || true
        done
        sleep 1
        for p in $pids; do
            if kill -0 "$p" 2>/dev/null; then
                kill -9 "$p" 2>/dev/null || true
            fi
        done
        log_success "Port ${port} successfully cleared."
    fi
}

# ── Prerequisites & Dependency Verification ───────────────────────────────────
check_system_tools() {
    log_info "Verifying system prerequisites..."

    # Check Python 3
    if ! command -v python3 >/dev/null 2>&1; then
        log_error "Python 3 is not installed or not in PATH. Please install Python >= 3.10."
        exit 1
    fi
    local py_version
    py_version=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    log_info "Detected Python ${py_version} (${GREEN}OK${NC})"

    # Check Node.js
    if ! command -v node >/dev/null 2>&1; then
        log_error "Node.js is not installed or not in PATH. Please install Node.js >= 18."
        exit 1
    fi
    local node_version
    node_version=$(node --version)
    log_info "Detected Node.js ${node_version} (${GREEN}OK${NC})"

    # Check npm
    if ! command -v npm >/dev/null 2>&1; then
        log_error "npm is not installed. Please install npm."
        exit 1
    fi
    local npm_version
    npm_version=$(npm --version)
    log_info "Detected npm ${npm_version} (${GREEN}OK${NC})"
}

setup_environment_files() {
    log_info "Checking environment configuration..."

    # Root .env
    if [[ ! -f "$ROOT_ENV" ]]; then
        if [[ -f "$ROOT_ENV_EXAMPLE" ]]; then
            log_warn ".env not found. Copying from .env.example..."
            cp "$ROOT_ENV_EXAMPLE" "$ROOT_ENV"
            log_success "Created .env configuration file."
        else
            log_error "Neither .env nor .env.example found in project root."
            exit 1
        fi
    fi

    # ── Critical: Ensure ENVIRONMENT is set to 'testing' for local dev ───────
    # Without this, the demo password fallback in auth_provider.py is disabled
    # and all login attempts will return "Incorrect email or password".
    local env_value
    env_value=$(grep -E '^ENVIRONMENT=' "$ROOT_ENV" | head -1 | cut -d'=' -f2 | tr -d '"' | tr -d "'" | tr -d '[:space:]' || true)
    if [[ "$env_value" == "production" ]]; then
        log_warn "ENVIRONMENT is set to 'production' — overriding to 'testing' for local developer mode."
        log_warn "(In production deployments, remove this override and set ENVIRONMENT=production manually.)"
        sed -i 's/^ENVIRONMENT=.*/ENVIRONMENT="testing"/' "$ROOT_ENV"
    elif [[ -z "$env_value" ]]; then
        log_warn "ENVIRONMENT not set in .env — defaulting to 'testing' for local dev."
        echo 'ENVIRONMENT="testing"' >> "$ROOT_ENV"
    fi

    # ── Ensure SECRET_KEY is populated ────────────────────────────────────────
    local secret_val
    secret_val=$(grep -E '^SECRET_KEY=' "$ROOT_ENV" | head -1 | cut -d'=' -f2 | tr -d '"' | tr -d "'" | tr -d '[:space:]' || true)
    if [[ -z "$secret_val" ]] || [[ "$secret_val" == "dev-changeme-please-set-a-real-secret-in-production" ]]; then
        local new_secret
        new_secret=$(python3 -c "import secrets; print(secrets.token_hex(32))" 2>/dev/null || head -c 32 /dev/urandom | base64 | head -c 64)
        if grep -qE '^SECRET_KEY=' "$ROOT_ENV"; then
            sed -i "s|^SECRET_KEY=.*|SECRET_KEY=\"${new_secret}\"|" "$ROOT_ENV"
        else
            echo "SECRET_KEY=\"${new_secret}\"" >> "$ROOT_ENV"
        fi
        log_success "Generated and saved a secure SECRET_KEY to .env."
    fi

    log_info "Root .env file is configured (${GREEN}OK${NC})"
    # Ensure required runtime directories
    mkdir -p "${BACKEND_DIR}/storage" "${BACKEND_DIR}/backups" "${BACKEND_DIR}/logs"

    # Frontend .env.local
    if [[ ! -f "$FRONTEND_ENV_LOCAL" ]]; then
        log_info "Creating default frontend local configuration (${FRONTEND_ENV_LOCAL})..."
        cat << 'EOF' > "$FRONTEND_ENV_LOCAL"
NEXT_PUBLIC_API_URL=http://localhost:3000
NEXT_PUBLIC_ENABLE_DEMO_LOGINS=true
BACKEND_URL=http://127.0.0.1:8000
EOF
        log_success "Created frontend/.env.local"
    fi
}

setup_backend_dependencies() {
    log_info "Verifying backend virtual environment..."

    if [[ ! -f "$VENV_PYTHON" ]]; then
        log_warn "Python virtual environment not found in ${VENV_DIR}."
        log_info "Creating virtual environment..."
        python3 -m venv "$VENV_DIR"
        log_success "Virtual environment created."
    fi

    # Check if backend dependencies need installation
    log_info "Verifying backend dependencies..."
    local needs_pip_install=0
    if ! "$VENV_PYTHON" -c "import uvicorn, fastapi, sqlalchemy, pydantic, alembic" >/dev/null 2>&1; then
        needs_pip_install=1
    fi

    # Or if requirements.txt is newer than installed packages record
    local req_stamp="${VENV_DIR}/.requirements.installed"
    if [[ ! -f "$req_stamp" ]] || [[ "${BACKEND_DIR}/requirements.txt" -nt "$req_stamp" ]]; then
        needs_pip_install=1
    fi

    if [[ $needs_pip_install -eq 1 ]]; then
        log_info "Installing / updating backend dependencies from requirements.txt..."
        "$VENV_PIP" install --upgrade pip >/dev/null 2>&1 || true
        "$VENV_PIP" install -r "${BACKEND_DIR}/requirements.txt"
        touch "$req_stamp"
        log_success "Backend dependencies successfully installed."
    else
        log_info "Backend dependencies verified (${GREEN}OK${NC})"
    fi
}

setup_database() {
    log_info "Verifying database schema and initial data..."
    (
        cd "$BACKEND_DIR"
        "$VENV_PYTHON" init_db_all.py
        "$VENV_PYTHON" seed_rbac.py
        "$VENV_PYTHON" seed.py
    )
    log_success "Database schema and seed data verified (${GREEN}OK${NC})"
}

setup_frontend_dependencies() {
    log_info "Verifying frontend dependencies..."
    local node_modules_dir="${FRONTEND_DIR}/node_modules"
    local stamp_file="${node_modules_dir}/.package-installed.stamp"
    local needs_npm_install=0

    if [[ ! -d "$node_modules_dir" ]]; then
        needs_npm_install=1
    elif [[ ! -f "$stamp_file" ]] || [[ "${FRONTEND_DIR}/package.json" -nt "$stamp_file" ]]; then
        needs_npm_install=1
    fi

    if [[ $needs_npm_install -eq 1 ]]; then
        log_info "Installing frontend dependencies with npm..."
        (
            cd "$FRONTEND_DIR"
            npm install
            touch "$stamp_file"
        )
        log_success "Frontend dependencies successfully installed."
    else
        log_info "Frontend node_modules verified (${GREEN}OK${NC})"
    fi
}

run_preflight_checks() {
    echo -e "\n${BOLD}[1/3] System & Environment Verification${NC}"
    check_system_tools
    setup_environment_files

    echo -e "\n${BOLD}[2/3] Backend & Database Initialization${NC}"
    setup_backend_dependencies
    setup_database

    echo -e "\n${BOLD}[3/3] Frontend Dependencies Verification${NC}"
    setup_frontend_dependencies

    echo ""
    log_success "All pre-flight checks and dependencies are ready!"
}

# ── Launch Execution Functions ────────────────────────────────────────────────

# ── Launch Backend Silently in Background ─────────────────────────────────────
start_backend_bg() {
    local log_file="${BACKEND_DIR}/logs/dev-backend.log"
    log_info "Starting FastAPI backend (background) on ${BOLD}http://127.0.0.1:8000${NC} ..."
    log_info "Backend log: ${DIM}${log_file}${NC}"
    mkdir -p "${BACKEND_DIR}/logs"
    (
        cd "$BACKEND_DIR"
        "$VENV_UVICORN" app.main:app --host 127.0.0.1 --port 8000 --reload \
            >> "$log_file" 2>&1
    ) &
    local backend_pid=$!
    CHILD_PIDS+=("$backend_pid")

    # Poll for readiness (up to 20s)
    log_info "Waiting for backend to initialize..."
    local retries=0
    while [[ $retries -lt 10 ]]; do
        sleep 2
        if curl -sf "http://127.0.0.1:8000/api/v1/health" >/dev/null 2>&1; then
            log_success "Backend is online at http://127.0.0.1:8000"
            return 0
        fi
        retries=$((retries + 1))
    done
    log_warn "Backend did not respond yet — Tauri will connect once it starts."
    log_info "Check log: ${DIM}${log_file}${NC}"
}

start_backend() {
    resolve_port 8000 "FastAPI Backend"
    log_info "Starting FastAPI Backend with live reload on ${BOLD}http://127.0.0.1:8000${NC} ..."
    log_info "Interactive API Docs available at ${BOLD}http://127.0.0.1:8000/docs${NC}"
    echo ""
    cd "$BACKEND_DIR"
    exec "$VENV_UVICORN" app.main:app --host 127.0.0.1 --port 8000 --reload
}

start_frontend() {
    resolve_port 3000 "Next.js Frontend"
    log_info "Starting Next.js Development Server on ${BOLD}http://localhost:3000${NC} ..."
    echo ""
    cd "$FRONTEND_DIR"
    exec npm run dev
}

start_full_stack() {
    resolve_port 8000 "FastAPI Backend"
    resolve_port 3000 "Next.js Frontend"

    log_info "Starting Bikita Minerals DWRMS Full Stack..."
    log_info "• FastAPI Backend: ${BOLD}http://127.0.0.1:8000${NC} (Docs: ${BOLD}/docs${NC})"
    log_info "• Next.js Frontend: ${BOLD}http://localhost:3000${NC}"
    log_info "Press ${BOLD}Ctrl+C${NC} to cleanly stop all services."
    echo ""

    # Stream with colored prefixes in a unified terminal
    # Backend process
    (
        cd "$BACKEND_DIR"
        "$VENV_UVICORN" app.main:app --host 127.0.0.1 --port 8000 --reload 2>&1 | while IFS= read -r line; do
            echo -e "${CYAN}${BOLD}[BACKEND]${NC}  $line"
        done
    ) &
    local backend_pid=$!
    CHILD_PIDS+=("$backend_pid")

    # Frontend process
    (
        cd "$FRONTEND_DIR"
        npm run dev 2>&1 | while IFS= read -r line; do
            echo -e "${MAGENTA}${BOLD}[FRONTEND]${NC} $line"
        done
    ) &
    local frontend_pid=$!
    CHILD_PIDS+=("$frontend_pid")

    # Wait for child processes
    wait "$backend_pid" "$frontend_pid" 2>/dev/null || true
}

start_tauri_desktop() {
    ensure_rust
    resolve_port 8000 "FastAPI Backend"
    resolve_port 3000 "Next.js / Tauri Dev Server"

    log_info "Starting Bikita Minerals DWRMS — Tauri Desktop Dev Mode"
    log_info "• FastAPI Backend: ${BOLD}http://127.0.0.1:8000${NC} (silent background)"
    log_info "• Tauri window will open with Next.js hot reload"
    log_info "Press ${BOLD}Ctrl+C${NC} or close the Tauri window to stop."
    echo ""

    start_backend_bg

    (
        cd "$FRONTEND_DIR"
        npm run tauri:window 2>&1 | while IFS= read -r line; do
            echo -e "${MAGENTA}${BOLD}[TAURI]${NC}    $line"
        done
    ) &
    local tauri_pid=$!
    CHILD_PIDS+=("$tauri_pid")

    wait "$tauri_pid" 2>/dev/null || true
}


show_menu() {
    banner
    echo -e "${BOLD}Select execution mode:${NC}\n"
    echo -e "  ${CYAN}[1]${NC} ${BOLD}Tauri Desktop${NC}      - Native desktop app (hot reload) ${GREEN}[DEFAULT]${NC}"
    echo -e "  ${CYAN}[2]${NC} ${BOLD}Web Stack${NC}          - FastAPI + Next.js in browser"
    echo -e "  ${CYAN}[3]${NC} ${BOLD}Backend Only${NC}       - FastAPI API server (:8000)"
    echo -e "  ${CYAN}[4]${NC} ${BOLD}Frontend Only${NC}      - Next.js browser app (:3000)"
    echo -e "  ${CYAN}[5]${NC} ${BOLD}Setup / Deps${NC}       - Verify & install all dependencies & init DB"
    echo -e "  ${CYAN}[6]${NC} ${BOLD}Exit${NC}\n"
    read -r -p "Enter choice [1-6] (default: 1 = Tauri): " choice
    choice="${choice:-1}"
    case "$choice" in
        1)
            run_preflight_checks
            start_tauri_desktop
            ;;
        2)
            run_preflight_checks
            start_full_stack
            ;;
        3)
            run_preflight_checks
            start_backend
            ;;
        4)
            run_preflight_checks
            start_frontend
            ;;
        5)
            run_preflight_checks
            log_success "Environment ready. You can now run: ./run.sh"
            ;;
        6|q|Q)
            echo "Exiting."
            exit 0
            ;;
        *)
            log_error "Invalid selection '${choice}'."
            exit 1
            ;;
    esac
}

show_help() {
    banner
    echo -e "Usage: ${BOLD}./run.sh${NC} [COMMAND]\n"
    echo -e "Commands:"
    echo -e "  ${CYAN}(default)${NC}           Tauri desktop dev mode (auto-installs Rust if needed)"
    echo -e "  ${CYAN}tauri, desktop${NC}     Tauri desktop application (default)"
    echo -e "  ${CYAN}web, all, stack${NC}    Web stack: FastAPI Backend + Next.js in browser"
    echo -e "  ${CYAN}backend, api${NC}       FastAPI backend server on :8000"
    echo -e "  ${CYAN}frontend${NC}           Next.js frontend server on :3000"
    echo -e "  ${CYAN}deps, setup${NC}        Verify & install dependencies and initialize database"
    echo -e "  ${CYAN}help, -h, --help${NC}   Show this help message\n"
    echo -e "Default credentials (testing mode):"
    echo -e "  ${CYAN}admin@bikita.com${NC}       / password123"
    echo -e "  ${CYAN}tech@bikita.com${NC}        / password123"
    echo -e "  ${CYAN}supervisor@bikita.com${NC}  / password123"
}

# ── Main Entry Point ──────────────────────────────────────────────────────────
main() {
    local cmd="${1:-}"
    case "$cmd" in
        ""|tauri|desktop)
            # Default: Tauri desktop dev mode
            banner
            run_preflight_checks
            start_tauri_desktop
            ;;
        web|all|dev|stack)
            banner
            run_preflight_checks
            start_full_stack
            ;;
        backend|api)
            banner
            run_preflight_checks
            start_backend
            ;;
        frontend)
            banner
            run_preflight_checks
            start_frontend
            ;;
        deps|setup|install)
            banner
            run_preflight_checks
            log_success "Setup complete."
            ;;
        menu)
            banner
            show_menu
            ;;
        help|-h|--help)
            show_help
            ;;
        *)
            log_error "Unknown option: '$cmd'"
            show_help
            exit 1
            ;;
    esac
}

main "$@"
