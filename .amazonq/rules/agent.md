✅ Universal Agent Guidelines (Coding)

Always Search Before You Build  

Search official docs, APIs, and libraries first.  

Use keywords like: “[tool] example” or “[task] site:github.com”.  

Prefer native solutions over adding dependencies.

Understand the Context First  

If editing a file:  

Read it fully and summarize its purpose.

If adding features:  

Map where it fits in the flow, state, or API layer.

Plan First, Code After  

Break features into sub-tasks.  

Outline steps:  

e.g., “Step 1: Fetch data → Step 2: Process → Step 3: Display.”

Chunk Responses  

Avoid sending huge code blocks.  

Use: “Here’s part 1 of 3” and pause for continuation.

Use Git Extensively  

Commit often with clear messages.  

Branch per feature/task.  

Check git status and git diff before committing.  

Roll back if complexity spirals.

Keep Code Self-Documenting  

Use descriptive names and small functions.  

Comment only non-obvious logic; use docstrings for major blocks.

Write Tests or Usage Examples  

Provide sample inputs/outputs or basic tests.  

Use any testing framework or logging as needed.

Optimize for Reusability  

Avoid hardcoding; use env vars and modular code.  

Leverage composables, hooks, or utilities.

Suggest Improvements/Alternatives  

Offer options:  

e.g., “X could improve performance over Y here.”

Respect Architecture  

Follow folder structure and naming conventions.  

Separate UI, logic, storage, and integrations.

Handle Errors Gracefully (New)  

Use try-catch and log meaningful errors.  

e.g., “Failed to fetch data: [reason].”

Consider Security (New)  

Sanitize inputs, secure APIs, and avoid exposing keys.  

Follow basic security best practices (e.g., OWASP).

Be Performance-Aware (New)  

Optimize for speed and resource use when it matters.  

e.g., Avoid nested loops in hot paths.

🧠 GLOBAL RULES (Applies to All Projects)

Always Start with Why  

Write a clear problem statement and goal.  

e.g., “This tool helps X by doing Y.”

Document Before Execution  

Create a PRD, architecture outline, and README.  

Keep them updated as you go.

Reusability First  

Build components/logic reusable across projects.  

e.g., A shared utils module.

Automate Repetitive Tasks  

Script boilerplate or repetitive setup.  

e.g., A setup script for new projects.

Don’t Overbuild  

Deliver an MVP first, then iterate.  

e.g., Core features now, polish later.

Track Every Idea  

Log ideas and blockers in a central place (e.g., markdown).  

Tag as #idea or #future.

Be Human-Aware  

Design for human intervention where needed.  

e.g., Manual review in AI flows.

Versioning & Git Discipline  

Branch per feature; use atomic, descriptive commits.  

e.g., feat: add login page.

Self-Review Regularly  

Weekly reflection on progress and pain points.  

e.g., “What worked? What didn’t?”

Protect Energy  

Switch tasks if stuck; check in weekly.

Communicate with Stakeholders (New)  

Update collaborators or clients on progress.  

e.g., Weekly status emails.

Plan for Backup and Recovery (New)  

Back up code and data; have a recovery plan.  

e.g., Git + cloud storage.