# Global Windsurf Rules File
These rules govern how Cascade behaves across all workspaces, ensuring consistent, efficient, and production-ready development for my portfolio projects (healthcare mobile app, SaaS chatbot builder, AI virtual office, self-hosted NotebookLM alternative). The goal is to complete MVPs, avoid endless iterations, and produce demo-ready code for showcasing to clients via YouTube and LinkedIn.

## Build and Testing Systems
1. **Frontend Build System**: Use Next.js for web and React Native/Expo for mobile. Leverage Vercel for deployment.
2. **Backend Build System**: Use FastAPI for Python-based APIs, deployed on Fly.io or Render.
3. **Testing Frameworks**:
   - Frontend: Jest for React/Next.js, React Testing Library for components.
   - Backend: pytest for FastAPI and LangChain pipelines.
   - Include basic assertions or mock data for every feature.
4. **Database and ORM**: Prefer Prisma for MongoDB/Postgres or Drizzle for lightweight Postgres with Supabase.

## File and API Restrictions
5. **Protected Files**:
   - Do not modify: `prisma/schema.prisma`, `.env`, `package.json`, `pyproject.toml` without explicit approval.
   - Reason: These files are critical and changes can break the project.
6. **Restricted APIs**:
   - Avoid deprecated APIs (e.g., Firebase v8, older LangChain modules).
   - Prefer stable, maintained libraries (e.g., LangChain v0.3+, LlamaIndex v0.11+).
7. **Dependency Management**:
   - Minimize dependencies; justify each addition.
   - e.g., Use native fetch instead of Axios for simple HTTP requests.

## Project Context
8. **Portfolio Projects**:
   - **Healthcare Mobile App**: React Native/Expo, NestJS, Google Gemini for OCR and health insights. Focus: MVP with OCR scanning and reminders.
   - **SaaS Chatbot Builder**: Next.js, FastAPI, LangChain for chatbot logic. Focus: Customizable chatbot creation and analytics.
   - **AI Virtual Office**: Next.js, Supabase, LangGraph for task automation. Focus: Task and calendar integration.
   - **NotebookLM Alternative**: FastAPI, Qdrant, Crawl4AI for research data. Focus: Text-based research tool.
9. **Prioritization**:
   - Focus on MVP features first (e.g., core functionality over polish).
   - Align features with client needs (solopreneurs, SMBs, startups).

## Coding Guidelines
10. **Search Before Build**:
    - Check official docs, GitHub, or Stack Overflow for existing solutions.
    - e.g., Search “[library] + [task] example” or “[task] site:*.edu”.
11. **Understand Context**:
    - Read the entire file before editing; summarize its purpose.
    - Map new features to the project’s flow (UI, logic, API, storage).
12. **Plan First**:
    - Break tasks into sub-tasks with clear steps.
    - e.g., “Step 1: Auth setup → Step 2: API integration → Step 3: UI.”
13. **Chunk Responses**:
    - Deliver code in parts (e.g., “Part 1 of 3”) to avoid overwhelming outputs.
14. **Git Discipline**:
    - Branch per feature (e.g., `feat/ocr-scanner`).
    - Commit often with messages like `feat: add user auth endpoint`.
    - Check `git status` and `git diff` before committing.
15. **Self-Documenting Code**:
    - Use descriptive names and small functions.
    - Add docstrings for complex logic; inline comments only when necessary.
16. **Error Handling**:
    - Use try-catch, log errors with context (e.g., “Failed to query DB: [reason]”).
    - Integrate Firebase or Sentry for error tracking.
17. **Security**:
    - Sanitize inputs, secure APIs with authentication, and avoid exposing keys.
    - Follow OWASP guidelines (e.g., validate inputs with Zod/Pydantic).
18. **Performance**:
    - Optimize for speed and resource use in critical paths.
    - e.g., Use lazy loading in Next.js, batch DB queries.

## AI Tool Integration
19. **Bolt.new (UI)**:
    - Use for rapid UI prototyping in React/Next.js/React Native.
    - Refactor output for modularity and responsiveness (e.g., with Dripsy/NativeWind).
20. **Cursor/Windsurf (Logic)**:
    - Generate modular, type-safe code (TypeScript for frontend, Pydantic for backend).
    - Reference PRDs in prompts for context.
    - e.g., “Generate a NestJS GraphQL API for [feature] using Prisma and MongoDB.”
21. **LangChain/LangGraph**:
    - Use for AI-driven features (e.g., chatbot logic, RAG pipelines).
    - Prefer Google Gemini for cost-effective embeddings and generation.

## Documentation and Showcasing
22. **Document Everything**:
    - Maintain a PRD, architecture outline, and README for each project.
    - Update README with setup, usage, and demo instructions.
23. **Demo-Ready Code**:
    - Ensure code is clean and commented for YouTube/LinkedIn demos.
    - Include usage examples or sample API calls.
24. **Showcase Preparation**:
    - Generate screenshots or videos (e.g., using OBS Studio) for each MVP.
    - Structure demos: Intro → Demo → Tech Stack → Call to Action.

## Project Management
25. **MVP First**:
    - Deliver core features before polish (e.g., OCR before analytics).
26. **Track Ideas**:
    - Log ideas, blockers, and enhancements in markdown or a tool like Notion.
27. **Stakeholder Communication**:
    - Share weekly updates with collaborators or clients.
    - e.g., “This week: Completed auth module; next: API integration.”
28. **Backup and Recovery**:
    - Back up code to GitHub and data to cloud storage (e.g., Supabase).
29. **User Feedback**:
    - Integrate feedback forms or analytics (e.g., Firebase) in MVPs.
30. **Compliance and Accessibility**:
    - Ensure GDPR compliance and WCAG accessibility (e.g., ARIA labels).

## Restrictions
31. **No Overwrites Without Approval**:
    - Cascade must prompt before overwriting critical files or logic.
32. **No Experimental Features**:
    - Avoid unstable APIs or libraries in alpha/beta stages.
33. **No Untracked Changes**:
    - All changes must be committed to Git with clear messages.

## Self-Reflection
34. **Weekly Review**:
    - Reflect on progress, blockers, and reusable components.
    - e.g., “What slowed me down? What’s reusable for next project?”
35. **Protect Energy**:
    - If stuck, switch tasks or projects; reassess weekly.