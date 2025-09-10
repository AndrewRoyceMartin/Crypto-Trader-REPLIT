#!/usr/bin/env bash
set -euo pipefail

# Start pyright fixer in background (non-blocking)
echo "🧹 Starting pyright fixer in background..."
./scripts/run_pyright_fixer.sh &

# Start the app in background
echo "Starting app..."
python -m gunicorn app:app -b 0.0.0.0:5000 --timeout 120 &
APP_PID=$!

# Give it a moment to boot
sleep 3

echo "Running self-check..."
python3 scripts/verify_runtime.py

echo "✅ Self-check passed. Attaching to app logs."
wait ${APP_PID}