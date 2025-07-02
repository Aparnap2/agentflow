# 🔍 Reality Check Protocol: Anti-Hallucination Framework

## 🎯 **Purpose: Prevent Implementation Hallucinations**

This protocol ensures every implementation step is grounded in actual codebase reality, not assumptions or wishful thinking.

---

## 🧠 **Pre-Implementation Reality Check**

### **Step 1: Codebase Audit**
```bash
# Before ANY implementation, run these commands:

# 1. Check current file structure
find . -name "*.py" -o -name "*.jsx" -o -name "*.js" | head -20

# 2. Verify what actually exists
ls -la frontend/src/pages/
ls -la backend/agents/
ls -la backend/flows/

# 3. Check current dependencies
cat frontend/package.json | grep -A 20 "dependencies"
cat backend/requirements.txt | head -10

# 4. Test current functionality
cd frontend && npm run dev &
cd backend && uvicorn main:app --reload &
curl http://localhost:8000/api/health
```

### **Step 2: Read Before Writing**
```markdown
MANDATORY: Before modifying any file, ALWAYS:
1. Read the entire file first
2. Understand its current purpose
3. Identify existing patterns
4. Note dependencies and imports
5. Test current functionality
```

### **Step 3: Document Current State**
```markdown
Create CURRENT_STATE.md with:
- ✅ What actually works right now
- ⚠️ What exists but has issues  
- ❌ What doesn't exist at all
- 🔧 What needs modification
- 📋 Dependencies required
```

---

## 📊 **Implementation Verification Matrix**

### **Before Each Change**
| Check | Command | Expected Result | Status |
|-------|---------|----------------|--------|
| Frontend builds | `npm run build` | No errors | ⏳ |
| Backend starts | `uvicorn main:app` | Server running | ⏳ |
| API responds | `curl localhost:8000/api/health` | 200 OK | ⏳ |
| Database connects | Check logs | No connection errors | ⏳ |
| Tests pass | `npm test` (if exists) | All tests green | ⏳ |

### **After Each Change**
| Check | Command | Expected Result | Status |
|-------|---------|----------------|--------|
| No build errors | `npm run build` | Clean build | ⏳ |
| No runtime errors | Check browser console | No red errors | ⏳ |
| API still works | Test endpoints | Same responses | ⏳ |
| New feature works | Manual testing | Feature functional | ⏳ |
| Old features work | Regression testing | No breaking changes | ⏳ |

---

## 🎯 **File-Specific Reality Checks**

### **Frontend Files**
```bash
# Before modifying React components:
# 1. Check if file exists
ls -la frontend/src/pages/StartPage.jsx

# 2. Read current content
cat frontend/src/pages/StartPage.jsx

# 3. Check imports and dependencies
grep -n "import" frontend/src/pages/StartPage.jsx

# 4. Verify component is used
grep -r "StartPage" frontend/src/

# 5. Test current functionality
# Navigate to the page and verify it works
```

### **Backend Files**
```bash
# Before modifying Python files:
# 1. Check if file exists
ls -la backend/agents/cofounder_agent.py

# 2. Read current content
cat backend/agents/cofounder_agent.py

# 3. Check imports and dependencies
grep -n "import\|from" backend/agents/cofounder_agent.py

# 4. Verify class is used
grep -r "CofounderAgent" backend/

# 5. Test current functionality
# Make API call and verify response
```

---

## 🔧 **Incremental Implementation Protocol**

### **Micro-Step Approach**
```markdown
Instead of: "Implement complete onboarding flow"
Do: 
1. Create basic OnboardingWizard component
2. Test it renders without errors
3. Add Step 1 with simple form
4. Test Step 1 works
5. Add Step 2 with basic questions
6. Test Step 2 works
7. Add Step 3 with team display
8. Test complete flow
9. Style and polish
10. Final integration testing
```

### **Commit Strategy**
```bash
# After each micro-step:
git add .
git commit -m "feat: [specific micro-change] - tested and working"

# Example commits:
# "feat: add basic OnboardingWizard component - renders without errors"
# "feat: add Step 1 idea input - form submission works"
# "feat: add Step 2 questions - option selection works"
```

---

## 📋 **Reality Check Checklists**

### **Before Starting Any Feature**
- [ ] I have read all related existing files
- [ ] I understand the current architecture
- [ ] I have tested what currently works
- [ ] I have identified what needs to change
- [ ] I have a specific, minimal implementation plan
- [ ] I know how to test the new feature
- [ ] I have a rollback plan if something breaks

### **During Implementation**
- [ ] I am making one small change at a time
- [ ] I am testing after each change
- [ ] I am committing working code frequently
- [ ] I am not breaking existing functionality
- [ ] I am following existing code patterns
- [ ] I am documenting what I'm changing

### **After Implementation**
- [ ] The new feature works as intended
- [ ] All existing features still work
- [ ] There are no console errors
- [ ] The build process succeeds
- [ ] I have tested on multiple screen sizes (if UI)
- [ ] I have updated relevant documentation

---

## 🚨 **Hallucination Warning Signs**

### **Red Flags to Watch For**
1. **Assuming files exist** without checking
2. **Assuming APIs work** without testing
3. **Planning complex features** without understanding current code
4. **Making multiple changes** without testing each one
5. **Ignoring error messages** or console warnings
6. **Not reading existing code** before modifying
7. **Assuming dependencies are installed** without verifying

### **When to Stop and Reality Check**
- When you get unexpected errors
- When existing features stop working
- When you're making assumptions about code structure
- When you haven't tested in >30 minutes
- When you're implementing >3 changes at once
- When you're not sure how something currently works

---

## 🎯 **Specific AgentFlow Reality Checks**

### **Current Architecture Verification**
```bash
# Verify agent system works
curl -X POST http://localhost:8000/api/conversation/start \
  -H "Content-Type: application/json" \
  -d '{"message": "test startup idea"}'

# Verify memory systems
curl http://localhost:8000/api/memory/shared-context

# Verify collaboration system
curl http://localhost:8000/api/collaboration/history

# Verify frontend pages
# Navigate to each route and verify it loads:
# http://localhost:3000/
# http://localhost:3000/dashboard
# http://localhost:3000/agents
# http://localhost:3000/reports
```

### **Component Verification**
```bash
# Check what components actually exist
find frontend/src/components -name "*.jsx" | sort

# Check what pages actually exist  
find frontend/src/pages -name "*.jsx" | sort

# Check what agents actually exist
find backend/agents -name "*_agent.py" | sort

# Check what APIs actually exist
grep -r "@app\." backend/ | grep -E "(get|post|put|delete)"
```

---

## 📊 **Progress Tracking Template**

### **Daily Reality Check Log**
```markdown
## Date: [YYYY-MM-DD]

### Pre-Implementation Audit
- [ ] Read all files I plan to modify
- [ ] Tested current functionality
- [ ] Documented what exists vs what's needed
- [ ] Created specific implementation plan

### Implementation Progress
- ✅ Completed: [specific changes made]
- 🔄 In Progress: [current task]
- ⚠️ Issues Found: [problems encountered]
- 🧪 Testing Status: [what was tested]

### Reality Check Results
- [ ] New code works as intended
- [ ] Existing functionality preserved
- [ ] No new errors introduced
- [ ] Performance not degraded

### Next Steps
- 📋 Tomorrow: [specific next tasks]
- 🎯 Focus: [main objective]
- ⚠️ Watch Out For: [potential issues]
```

---

## 🎯 **Success Metrics**

### **Quality Indicators**
- **Zero Breaking Changes**: Existing features continue to work
- **Incremental Progress**: Each commit adds working functionality
- **Clean Error Logs**: No new console errors or warnings
- **Performance Maintained**: Load times don't increase
- **Documentation Updated**: Changes are documented

### **Velocity Indicators**
- **Consistent Daily Progress**: Something working added each day
- **Predictable Outcomes**: Features work as planned
- **Minimal Debugging Time**: <20% of time spent fixing issues
- **High Confidence**: Know exactly what each change does

This protocol ensures every implementation step is grounded in reality and delivers reliable, working progress toward the production-ready AgentFlow platform! 🎯