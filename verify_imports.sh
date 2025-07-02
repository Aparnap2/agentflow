#!/bin/bash

# Script to verify all imports are fixed

echo "🔍 Checking for remaining apiMethods imports..."

# Check for apiMethods imports
REMAINING=$(grep -r "apiMethods" --include="*.jsx" --include="*.js" frontend/src/ | grep -v "api.js")

if [ -z "$REMAINING" ]; then
  echo "✅ All imports fixed successfully!"
else
  echo "❌ Found remaining apiMethods imports:"
  echo "$REMAINING"
  exit 1
fi

echo "✅ Import verification complete!"