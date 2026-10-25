#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
cd "$DIR"

echo "============================================================"
echo "               SIGNAL HUNT - BACKEND SERVER                 "
echo "============================================================"

# Check Python 3
if ! command -v python3 &> /dev/null; then
    echo "[-] Error: python3 is required but not installed."
    echo "    Please install Python 3.10+ (e.g., sudo apt install python3 python3-venv)"
    exit 1
fi

# Create virtual environment if missing
if [ ! -d ".venv" ]; then
    echo "[+] Creating virtual environment (.venv)..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "[+] Activating virtual environment..."
source .venv/bin/activate

# Install requirements
echo "[+] Installing / verifying Python dependencies..."
pip install -q -r requirements.txt

# Load environment variables if .env exists
if [ -f ".env" ]; then
    echo "[+] Loading environment variables from .env..."
    export $(grep -v '^#' .env | xargs)
fi

export ADMIN_PASSWORD="${ADMIN_PASSWORD:-ISLIEEEECELL}"
export DATABASE_PATH="${DATABASE_PATH:-signalhunt.db}"
export MAX_TEAMS="${MAX_TEAMS:-4}"

echo "------------------------------------------------------------"
echo "  Organizer Password : $ADMIN_PASSWORD"
echo "  Database File      : $DATABASE_PATH"
echo "  Max Teams Allowed  : $MAX_TEAMS"
echo "  Server URL         : http://0.0.0.0:8000"
echo "  API Docs (Swagger) : http://0.0.0.0:8000/docs"
echo "------------------------------------------------------------"
echo "[+] Starting Uvicorn server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
