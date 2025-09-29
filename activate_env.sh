#!/bin/bash
# Automatic activation script for PyNetro virtual environment

# Check if we're already in a virtual environment
if [[ -z "$VIRTUAL_ENV" ]]; then
    # Look for .venv file in current or parent directory
    if [[ -f ".venv/bin/activate" ]]; then
        echo "🐍 Activating PyNetro virtual environment..."
        source .venv/bin/activate
        echo "✅ Virtual environment activated: $(python --version)"
        echo "📦 Location: $VIRTUAL_ENV"
    elif [[ -f "../.venv/bin/activate" ]]; then
        echo "🐍 Activating PyNetro virtual environment (parent directory)..."
        source ../.venv/bin/activate
        echo "✅ Virtual environment activated: $(python --version)"
        echo "📦 Location: $VIRTUAL_ENV"
    else
        echo "⚠️ Virtual environment .venv not found"
        echo "💡 To create: python -m venv .venv && source .venv/bin/activate"
    fi
else
    echo "✅ Virtual environment already active: $(basename $VIRTUAL_ENV)"
fi