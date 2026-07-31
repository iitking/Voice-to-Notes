#!/bin/bash

# ==========================================================
# Voice to Notes AI - One-Click Launcher (macOS)
# ==========================================================

set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "🚀 Starting Voice to Notes AI..."

# 1. Check & Start PostgreSQL
echo "📦 [1/4] Checking PostgreSQL..."
if ! /opt/homebrew/opt/postgresql@16/bin/pg_isready -q 2>/dev/null; then
    echo "Starting PostgreSQL service..."
    /opt/homebrew/opt/postgresql@16/bin/pg_ctl -D /opt/homebrew/var/postgresql@16 -l /opt/homebrew/var/postgresql@16/server.log start || true
    sleep 2
fi
echo "✅ PostgreSQL is ready."

# 2. Check & Start Ollama
echo "🧠 [2/4] Checking Ollama..."
if ! curl -s http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
    echo "Starting Ollama in background..."
    ollama serve >/dev/null 2>&1 &
    sleep 3
fi
echo "✅ Ollama is ready."

# 3. Start Backend
echo "⚡ [3/4] Starting FastAPI backend on http://127.0.0.1:8000..."
export PYTHONPATH="$DIR/backend"
"$DIR/backend/.venv/bin/uvicorn" app.main:app --host 127.0.0.1 --port 8000 --reload > backend.log 2>&1 &
BACKEND_PID=$!

# 4. Start Frontend
echo "💻 [4/4] Starting React Vite frontend on http://localhost:5173..."
cd "$DIR/frontend"
npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
cd "$DIR"

echo ""
echo "=========================================================="
echo "🎉 Voice to Notes AI is RUNNING!"
echo "👉 Open Web App: http://localhost:5173"
echo "👉 API Docs:     http://127.0.0.1:8000/docs"
echo "=========================================================="
echo "Press Ctrl+C to stop both servers."

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true; echo 'Servers stopped.'; exit 0" SIGINT SIGTERM

wait
