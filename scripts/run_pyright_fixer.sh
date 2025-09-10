#!/usr/bin/env bash
# Auto-run pyright fixer on startup
set -euo pipefail

echo "🧹 Running pyright fixer in background..."

# Run the fixer in background
python3 scripts/fix_pyright_extended.py > /tmp/pyright_fixer.log 2>&1 &
FIXER_PID=$!

echo "✅ Pyright fixer started (PID: $FIXER_PID)"
echo "   Log: /tmp/pyright_fixer.log"
echo "   To check status: ps -p $FIXER_PID"

# Optional: wait for completion and show result
if [ "${1:-}" = "--wait" ]; then
    echo "⏳ Waiting for fixer to complete..."
    wait $FIXER_PID
    echo "✅ Pyright fixer completed!"
    cat /tmp/pyright_fixer.log
fi