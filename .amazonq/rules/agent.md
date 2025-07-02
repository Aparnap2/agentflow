# ✅ Vibe Coding Rules & Guidelines

> **Philosophy**: Code with intention, ship with confidence, iterate with purpose.

---

## 📋 Implementation Tracking

### Current Phase
- [ ] **Phase 1**: Setup & Foundation
- [ ] **Phase 2**: Core Development  
- [ ] **Phase 3**: Testing & Optimization
- [ ] **Phase 4**: Documentation & Deployment

### Project Status
```markdown
Project: _______________
Status: [ ] Planning | [ ] In Progress | [ ] Review | [ ] Complete
Last Updated: ___________
Next Milestone: _________
```

---

## 🔧 Universal Agent Guidelines (Coding)

### 1. Always Search Before You Build
- **Search Strategy**: Official docs, APIs, and libraries first
- **Search Patterns**: 
  - `"[tool] example"`
  - `"[task] site:github.com"`
  - `"[framework] best practices"`
- **Priority**: Native solutions > Third-party dependencies
- **Documentation**: Track search results in `research.md`

### 2. Understand Context First
**When editing existing files:**
- [ ] Read file completely
- [ ] Summarize purpose and current functionality
- [ ] Document dependencies and relationships

**When adding features:**
- [ ] Map integration points (flow, state, API layer)
- [ ] Identify potential conflicts
- [ ] Plan rollback strategy

### 3. Plan First, Code After
**Feature Breakdown Process:**
1. **Decompose**: Break into atomic sub-tasks
2. **Sequence**: Define step-by-step flow
   - Example: `Step 1: Fetch data → Step 2: Process → Step 3: Display`
3. **Estimate**: Time and complexity assessment
4. **Document**: Record in `planning.md`

### 4. Chunk Responses
- **Rule**: Avoid massive code blocks
- **Pattern**: "Here's part X of Y" with continuation prompts
- **Benefits**: Better review, easier debugging, clearer progress

### 5. Git Discipline
**Commit Strategy:**
- [ ] Frequent commits with descriptive messages
- [ ] One feature per branch
- [ ] Always check `git status` and `git diff` before committing
- [ ] Use conventional commit format: `type: description`

**Branch Naming:**
- `feature/feature-name`
- `fix/bug-description`
- `docs/update-readme`

**Rollback Protocol:**
- If complexity spirals → immediate rollback
- Document lessons learned

### 6. Self-Documenting Code
**Code Quality Standards:**
- **Naming**: Descriptive variables and function names
- **Functions**: Small, single-purpose functions
- **Comments**: Only for non-obvious logic
- **Docstrings**: For all major blocks and modules

### 7. Testing & Examples
**Requirements:**
- [ ] Provide sample inputs/outputs
- [ ] Write basic tests for core functionality
- [ ] Include usage examples in README
- [ ] Use appropriate testing framework

### 8. Optimize for Reusability
**Design Principles:**
- [ ] No hardcoded values (use env vars)
- [ ] Modular, composable code
- [ ] Shared utilities and hooks
- [ ] Configuration-driven behavior

### 9. Continuous Improvement
**Regular Practice:**
- [ ] Suggest performance improvements
- [ ] Offer alternative approaches
- [ ] Document trade-offs and decisions

### 10. Respect Architecture
**Consistency Rules:**
- [ ] Follow existing folder structure
- [ ] Maintain naming conventions
- [ ] Separate concerns: UI | Logic | Storage | Integrations
- [ ] Honor established patterns

### 11. Error Handling
**Error Management:**
- [ ] Use try-catch blocks appropriately
- [ ] Log meaningful error messages
- [ ] Provide user-friendly error states
- [ ] Include recovery mechanisms

**Error Message Format:**
```
"Failed to [action]: [specific reason] - [next steps]"
```

### 12. Security Considerations
**Security Checklist:**
- [ ] Sanitize all inputs
- [ ] Secure API endpoints
- [ ] Protect sensitive keys/tokens
- [ ] Follow OWASP guidelines
- [ ] Regular security reviews

### 13. Performance Awareness
**Optimization Guidelines:**
- [ ] Profile before optimizing
- [ ] Avoid nested loops in hot paths
- [ ] Optimize for critical user journeys
- [ ] Monitor resource usage
- [ ] Implement lazy loading where appropriate

---

## 🧠 Global Rules (All Projects)

### 1. Start with Why
**Problem Statement Template:**
```markdown
## Problem
What specific problem does this solve?

## Goal  
What success looks like?

## Impact
Who benefits and how?
```

### 2. Document Before Execution
**Required Documents:**
- [ ] `README.md` - Project overview and setup
- [ ] `PLANNING.md` - Feature roadmap and decisions
- [ ] `ARCHITECTURE.md` - System design and patterns
- [ ] `CHANGELOG.md` - Version history and updates

### 3. Reusability First
**Reusable Components Strategy:**
- [ ] Build shared utilities library
- [ ] Create component templates
- [ ] Establish common patterns
- [ ] Document reusable patterns

### 4. Automate Repetitive Tasks
**Automation Targets:**
- [ ] Project setup scripts
- [ ] Build and deployment processes
- [ ] Testing workflows
- [ ] Code formatting and linting

### 5. MVP-First Approach
**Development Phases:**
1. **Core Features** - Essential functionality only
2. **User Feedback** - Gather real usage data
3. **Iteration** - Improve based on feedback
4. **Polish** - UI/UX enhancements

### 6. Idea Management
**Tracking System:**
- **Location**: `ideas.md` or project management tool
- **Tagging**: `#idea`, `#future`, `#blocker`, `#feedback`
- **Review**: Weekly idea review and prioritization

### 7. Human-Centered Design
**Human Intervention Points:**
- [ ] Manual review processes
- [ ] Approval workflows
- [ ] Error handling escalation
- [ ] Configuration management

### 8. Version Control Excellence
**Git Workflow:**
```bash
# Feature development
git checkout -b feature/new-feature
git add .
git commit -m "feat: add new feature functionality"
git push origin feature/new-feature

# Create PR, review, merge
```

### 9. Regular Self-Review
**Weekly Review Template:**
```markdown
## Week of [Date]

### ✅ Completed
- 

### 🔄 In Progress
- 

### 🚫 Blockers
- 

### 💡 Learnings
- 

### 📋 Next Week
- 
```

### 10. Energy Management
**Productivity Guidelines:**
- [ ] Switch tasks when stuck (> 30 min)
- [ ] Take breaks every 2 hours
- [ ] Weekly progress check-ins
- [ ] Celebrate small wins

### 11. Stakeholder Communication
**Communication Schedule:**
- **Daily**: Progress updates in team chat
- **Weekly**: Status email to stakeholders
- **Milestone**: Demo and feedback sessions

**Update Template:**
```markdown
## Weekly Status Update

**Progress**: What was accomplished
**Blockers**: Current challenges
**Next**: Upcoming priorities
**ETA**: Timeline updates
```

### 12. Backup & Recovery
**Data Protection:**
- [ ] Git repositories with remote backups
- [ ] Cloud storage for assets
- [ ] Environment configuration backups
- [ ] Recovery testing quarterly

---

## 📊 Project Implementation Template

### Phase Planning
```markdown
## Phase 1: Foundation (Week 1-2)
- [ ] Project setup and configuration
- [ ] Basic architecture implementation
- [ ] Development environment setup
- [ ] Initial documentation

## Phase 2: Core Development (Week 3-6)  
- [ ] Core feature implementation
- [ ] Basic testing setup
- [ ] Error handling implementation
- [ ] Performance optimization

## Phase 3: Integration & Testing (Week 7-8)
- [ ] Integration testing
- [ ] User acceptance testing
- [ ] Performance testing
- [ ] Security review

## Phase 4: Deployment & Documentation (Week 9-10)
- [ ] Production deployment
- [ ] Final documentation
- [ ] Team training
- [ ] Post-launch monitoring
```

### Success Metrics
- [ ] **Code Quality**: Test coverage > 80%
- [ ] **Performance**: Load time < 3s
- [ ] **Reliability**: Uptime > 99.9%
- [ ] **User Experience**: User satisfaction > 4.5/5
- [ ] **Maintainability**: Time to implement new features

---

## 🎯 Quick Reference Checklist

**Before Starting Any Task:**
- [ ] Search for existing solutions
- [ ] Understand the context
- [ ] Create implementation plan
- [ ] Set up proper branching

**During Development:**
- [ ] Commit frequently
- [ ] Write self-documenting code
- [ ] Handle errors gracefully
- [ ] Consider security implications

**Before Completion:**
- [ ] Test thoroughly
- [ ] Update documentation
- [ ] Review for reusability
- [ ] Plan next steps

---

*Last Updated: [Date]*  
*Version: 1.0*