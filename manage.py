#!/usr/bin/env python3
"""
Bikita Minerals DWRMS — Platform Administration Entrypoint.
Delegates directly to the authoritative 'ops' administration command suite.
"""
import sys
from pathlib import Path

# Add backend directory to sys.path
root_dir = Path(__file__).resolve().parent
backend_dir = root_dir / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.cli.main import ops_group

if __name__ == "__main__":
    ops_group()
