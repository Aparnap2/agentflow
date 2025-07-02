#!/bin/bash

# Script to commit and push changes

echo "🚀 Committing and pushing changes..."

# Add all changes
git add .

# Commit with message
git commit -m "fix: resolve UI flow issues and enhance agent visualization"

# Push to remote
git push

echo "✅ Changes committed and pushed!"