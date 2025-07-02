#!/bin/bash

# Cleanup script for UI files

echo "🧹 Cleaning up unnecessary UI files..."

# Create backup directory
mkdir -p .backup/frontend

# Move unnecessary files to backup
echo "📁 Moving unnecessary files to backup..."

# Backup unused enhanced components
mv frontend/src/EnhancedApp.jsx .backup/frontend/ 2>/dev/null || true
mv frontend/src/SimpleEnhancedApp.jsx .backup/frontend/ 2>/dev/null || true
mv frontend/src/components/WorkflowLayout.jsx .backup/frontend/ 2>/dev/null || true
mv frontend/src/components/WorkflowSidebar.jsx .backup/frontend/ 2>/dev/null || true
mv frontend/src/components/AgentTransition.jsx .backup/frontend/ 2>/dev/null || true
mv frontend/src/pages/EnhancedConversationPage.jsx .backup/frontend/ 2>/dev/null || true
mv frontend/src/pages/ExecutionPage.jsx .backup/frontend/ 2>/dev/null || true
mv frontend/src/pages/ResultsPage.jsx .backup/frontend/ 2>/dev/null || true
mv frontend/src/contexts/WorkflowContext.jsx .backup/frontend/ 2>/dev/null || true

# Keep useful components
# - EnhancedAgentCard.jsx - Can be used to replace AgentCard
# - api.js - Unified API client

echo "✅ UI cleanup complete!"