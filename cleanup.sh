#!/bin/bash

# Cleanup script to remove unnecessary files and reduce complexity

echo "🧹 Cleaning up unnecessary files to reduce complexity..."

# Create backup directory
mkdir -p .backup

# Move unnecessary MD files to backup
echo "📁 Moving unnecessary MD files to backup..."
mv ENHANCED_PRD.md .backup/ 2>/dev/null || true
mv FIXES_TRACKER.md .backup/ 2>/dev/null || true
mv FRONTEND_ALIGNMENT.md .backup/ 2>/dev/null || true
mv FRONTEND_REFACTOR_PLAN.md .backup/ 2>/dev/null || true
mv IMPLEMENTATION_EXECUTION_PLAN.md .backup/ 2>/dev/null || true
mv IMPLEMENTATION_STATUS.md .backup/ 2>/dev/null || true
mv IMPLEMENTATION_TRACKER.md .backup/ 2>/dev/null || true
mv STRATEGIC_ROADMAP.md .backup/ 2>/dev/null || true

# Keep only essential MD files
echo "📄 Keeping only essential MD files..."
# README.md - Main documentation
# FINAL_IMPLEMENTATION_SUMMARY.md - Final summary
# REALITY_CHECK_PROTOCOL.md - Reality check protocol
# UI_UX_ENHANCEMENT.md - UI/UX enhancement documentation
# IMPLEMENTATION_COMPLETE.md - Implementation completion status

# Create a single consolidated documentation file
echo "📝 Creating consolidated documentation..."
cat > DOCUMENTATION.md << EOL
# 🚀 AgentFlow Documentation

This file consolidates all essential documentation for the AgentFlow project.

## 📋 Table of Contents

1. [Overview](#overview)
2. [Implementation Summary](#implementation-summary)
3. [UI/UX Enhancement](#uiux-enhancement)
4. [Reality Check Protocol](#reality-check-protocol)
5. [Setup Instructions](#setup-instructions)

## Overview

AgentFlow is a production-ready AI platform where 8 specialized agents collaborate to analyze, plan, and execute your startup vision. From initial concept to comprehensive business reports, experience the power of AI-driven entrepreneurship.

$(cat README.md | grep -v "# AgentFlow" | grep -v "Table of Contents")

## Implementation Summary

$(cat FINAL_IMPLEMENTATION_SUMMARY.md | grep -v "# AgentFlow")

## UI/UX Enhancement

$(cat UI_UX_ENHANCEMENT.md | grep -v "# AgentFlow")

## Reality Check Protocol

$(cat REALITY_CHECK_PROTOCOL.md | grep -v "# Reality Check Protocol")

## Setup Instructions

### Quick Start

\`\`\`bash
# Start backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload

# Start frontend
cd frontend
pnpm install
pnpm dev
\`\`\`

### One-Command Startup

\`\`\`bash
./start_agentflow.sh
\`\`\`
EOL

echo "✅ Cleanup complete!"