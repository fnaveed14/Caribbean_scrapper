#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────
#  Caribbean Data Scraper — launcher (Mac / Linux)
#  Double-click this file OR run:  bash run.sh
# ─────────────────────────────────────────────────────────────────

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "================================================"
echo "  🌊  Caribbean Regional Report Data Scraper"
echo "================================================"
echo ""

# Check Python 3
if ! command -v python3 &>/dev/null; then
    echo "❌  Python 3 not found."
    echo "    Install from https://www.python.org/downloads/"
    read -p "Press Enter to exit..."
    exit 1
fi

PYTHON=$(command -v python3)
echo "✅  Python: $($PYTHON --version)"

# Create venv if not present
if [ ! -d ".venv" ]; then
    echo ""
    echo "📦  Creating virtual environment (first-time setup)..."
    $PYTHON -m venv .venv
fi

# Activate
source .venv/bin/activate

# Install / upgrade packages
echo ""
echo "📦  Installing / checking packages..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

echo ""
echo "🚀  Launching app — opening in your browser..."
echo "    (press Ctrl+C to stop)"
echo ""

streamlit run app.py \
    --server.headless false \
    --server.port 8501 \
    --browser.gatherUsageStats false
