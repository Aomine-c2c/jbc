#!/usr/bin/env bash
# ==============================================================================
# BIKITA MINERALS DWRMS — AUTHORITATIVE DEVELOPER STACK LAUNCHER
#
# Usage:
#   ./run.sh                  Interactive selection menu
#   ./run.sh all              Launch full stack (FastAPI Backend + Next.js Frontend)
#   ./run.sh backend          Launch Backend API only (FastAPI with hot reload)
#   ./run.sh frontend         Launch Frontend Web only (Next.js dev server)
#   ./run.sh tauri            Launch Desktop environment (FastAPI + Tauri)
#   ./run.sh deps             Verify and install all dependencies & init DB
#   ./run.sh help             Display usage instructions
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
    else
        log_info "Root .env file is present (${GREEN}OK${NC})"
    fi

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
    )
    log_success "Database schema verified (${GREEN}OK${NC})"
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
    resolve_port 8000 "FastAPI Backend"
    resolve_port 3000 "Next.js Frontend"

    if ! command -v cargo >/dev/null 2>&1; then
        log_warn "Rust/Cargo not found in PATH. Tauri requires Rust."
        log_info "If installed in ~/.cargo/bin, ensuring PATH includes it..."
        export PATH="${HOME}/.cargo/bin:${PATH}"
        if ! command -v cargo >/dev/null 2>&1; then
            log_error "Cargo is still not found. Please install Rust via: curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh"
            exit 1
        fi
    fi

    log_info "Starting Backend & Tauri Desktop Development Environment..."
    log_info "Press ${BOLD}Ctrl+C${NC} to stop."
    echo ""

    (
        cd "$BACKEND_DIR"
        "$VENV_UVICORN" app.main:app --host 127.0.0.1 --port 8000 --reload 2>&1 | while IFS= read -r line; do
            echo -e "${CYAN}${BOLD}[BACKEND]${NC}  $line"
        done
    ) &
    local backend_pid=$!
    CHILD_PIDS+=("$backend_pid")

    (
        cd "$FRONTEND_DIR"
        npm run tauri:dev 2>&1 | while IFS= read -r line; do
            echo -e "${MAGENTA}${BOLD}[TAURI]${NC}    $line"
        done
    ) &
    local tauri_pid=$!
    CHILD_PIDS+=("$tauri_pid")

    wait "$backend_pid" "$tauri_pid" 2>/dev/null || true
}

show_menu() {
    banner
    echo -e "${BOLD}Select execution mode:${NC}\n"
    echo -e "  ${CYAN}[1]${NC} ${BOLD}Full Stack${NC}         - Run FastAPI Backend & Next.js Frontend together"
    echo -e "  ${CYAN}[2]${NC} ${BOLD}Backend Only${NC}       - Run FastAPI API server with live reload (:8000)"
    echo -e "  ${CYAN}[3]${NC} ${BOLD}Frontend Only${NC}      - Run Next.js web application dev server (:3000)"
    echo -e "  ${CYAN}[4]${NC} ${BOLD}Tauri Desktop${NC}      - Run Backend & Tauri Desktop App"
    echo -e "  ${CYAN}[5]${NC} ${BOLD}Setup / Deps${NC}       - Verify & install all dependencies & init DB"
    echo -e "  ${CYAN}[6]${NC} ${BOLD}Exit${NC}\n"
    read -r -p "Enter choice [1-6] (default: 1): " choice
    choice="${choice:-1}"
    case "$choice" in
        1)
            run_preflight_checks
            start_full_stack
            ;;
        2)
            run_preflight_checks
            start_backend
            ;;
        3)
            run_preflight_checks
            start_frontend
            ;;
        4)
            run_preflight_checks
            start_tauri_desktop
            ;;
        5)
            run_preflight_checks
            log_success "Environment ready. You can now run: ./run.sh all"
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
    echo -e "  ${CYAN}all, dev, stack${NC}    Start full stack (FastAPI Backend + Next.js Frontend)"
    echo -e "  ${CYAN}backend, api${NC}       Start FastAPI backend server on :8000"
    echo -e "  ${CYAN}frontend, web${NC}      Start Next.js frontend server on :3000"
    echo -e "  ${CYAN}tauri, desktop${NC}     Start Tauri desktop application environment"
    echo -e "  ${CYAN}deps, setup${NC}        Verify & install dependencies and initialize database"
    echo -e "  ${CYAN}help, -h, --help${NC}   Show this help message\n"
    echo -e "If no command is provided, an interactive selection menu is shown."
}

# ── Main Entry Point ──────────────────────────────────────────────────────────
main() {
    local cmd="${1:-}"
    case "$cmd" in
        ""|menu)
            show_menu
            ;;
        all|dev|stack)
            banner
            run_preflight_checks
            start_full_stack
            ;;
        backend|api)
            banner
            run_preflight_checks
            start_backend
            ;;
        frontend|web)
            banner
            run_preflight_checks
            start_frontend
            ;;
        tauri|desktop)
            banner
            run_preflight_checks
            start_tauri_desktop
            ;;
        deps|setup|install)
            banner
            run_preflight_checks
            log_success "Setup complete."
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
