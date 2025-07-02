

---

# 🧠 Final PRD: `agentflow` — Virtual AI Office Platform

### 📅 Version: 1.3

### 🧑 Owner: Aparna Pradhan

### 🎯 Goal: A full-stack async AI office where intelligent agents (like Cofounder, Manager, Finance, etc.) collaborate to simulate a startup team with **shared memory**, **tool-driven reasoning**, and **human-in-the-loop approvals**.

Built for portfolio/freelance showcasing, not commercial use.

---

## 🔧 Tech Stack

| Layer               | Tech                                  | Purpose                                   |
|:--------------------|:--------------------------------------|:------------------------------------------|
| Frontend            | React + Vite + Tailwind CSS           | Interface and agent visualizations        |
| Backend             | FastAPI (Python), Pandas              | API, orchestration, data manipulation     |
| Agents              | LangGraph + LangChain                 | Agent personality, flow & memory          |
| Reporting           | Seaborn, Matplotlib, WeasyPrint       | Charting, PDF generation, rich reports    |
| Memory (Structured) | Neo4j                                 | Agent memory + cross-agent shared context |
| Memory (Semantic)   | Qdrant (free-tier)                    | Semantic document search, RAG             |
| Web Crawling        | Crawl4AI                              | Web data extraction tool                  |
| LLM Runtime         | OpenRouter                            | Agent LLMs (e.g., Gemini, Deepseek)       |
| Storage             | Local YAML, CSV, PDF, HTML, PNG       | Rich outputs, auth, config                |

---

## 👥 Agent Team (MVP)

| Agent            | Description                                     |
|:-----------------|:------------------------------------------------|
| 🧠 **Cofounder** | Captures vision, goals, target users            |
| 🧭 **Manager**   | Breaks vision into workstreams + assigns agents |
| 🎯 **Product**   | Defines MVP, features, personas                 |
| 💸 **Finance**   | Simulates budget, ROI, revenue options          |
| 📣 **Marketing** | Plans content, SEO, outreach                    |
| ⚖️ **Legal**     | Drafts ToS/Privacy + checks compliance          |
| 📈 **Sales**     | Creates sales forecasts and strategies          |

---

## 🧰 Agent Toolkits (Bound via LangChain tools or internal functions)

| Agent         | Tools Accessed                                                              |
|:--------------|:----------------------------------------------------------------------------|
| **Cofounder** | `LLM reasoning`, `memory.write`, `memory.query`                             |
| **Manager**   | `memory.read_all`, `task.assign`, `report.compile_all`, `report.export_pdf` |
| **Product**   | `rag.search`, `persona.create`, `plan.export_yaml`, `chart.gantt`           |
| **Finance**   | `mock_finance_call`, `web.fetch`, `chart.generate_seaborn`, `report.export_csv` |
| **Marketing** | `web.crawl`, `content.generate_html`, `seo.analyze`, `content.export_md`    |
| **Legal**     | `compliance.check`, `document.generate_pdf`, `regulatory.validate`          |
| **Sales**     | `crm.query`, `forecast.generate`, `report.export_csv`                       |

> 🧠 All agents use `OpenRouter` via LangChain wrappers for reasoning.

---

## 🧠 Memory System Architecture

| Layer                             | Description                                                                                                   |
| --------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| 🔒 **Private Memory** (per agent) | Stored in Neo4j. Holds internal thoughts, drafts, partial results. Queried only by that agent.                |
| 🌐 **Shared Global Context**      | Also Neo4j. Final memory nodes written only after approval or confidence threshold. Shared across all agents. |
| 🔍 **Semantic Vector Memory**     | Qdrant. Used for embedding search, RAG (Product, Marketing, Legal)                                            |
| 🗃️ **Outputs Folder**            | JSON/YAML files: exported from final memory nodes. Synced to UI.                                              |

> All memory is fully **traceable** — logs show *who wrote what, when, why, and with what source*.

---

## 🎭 LangGraph: Agent Personalities & Behaviors

LangGraph nodes for each agent define:

| Property                        | Implementation                                                                         |
|:--------------------------------|:---------------------------------------------------------------------------------------|
| **Prompt Style**                | Defined per agent (e.g., Cofounder is conversational, Legal is strict)                 |
| **Retry Logic**                 | Built into the core LangGraph workflow for error handling                              |
| **Trigger Conditions**          | Context-based execution; agents run when their inputs are available in shared memory   |
| **Feedback Hooks**              | The approval system allows agents to pause and request human input                     |
| **Priority/Confidence Routing** | If an agent's confidence is below a threshold (e.g., 60%), it triggers manual approval |

---

## 🔄 Coordination Model

### LangGraph DAG

```plaintext
[ User ] ──▶ [ Cofounder ]
              ↓
         [ Manager ]
              ↓
 ┌────────┬────────┬────────┬────────┐
 ↓        ↓        ↓        ↓        ↓
Product  Finance  Marketing Legal Sales
└────────┴────────┴────────┴────────┘
```
Product  Finance  Marketing Legal
 └────────────┬────────────┘
              ↓
        [ Shared Context ]
```

* Cofounder & Manager run sequentially
* All specialist agents run **in parallel**
* They **read from shared context** + **write own memory**
* Agents may **query** each other’s outputs
* Final export happens only after approval

---

## 🧑‍💻 UI/UX Workflow

### Pages & Components

| Route       | Components                                           | Purpose                   |
|:------------|:-----------------------------------------------------|:--------------------------|
| `/start`    | `ProjectForm`, `TriggerCofounder`                    | Start project, enter idea |
| `/vision`   | `VisionViewer`, `ManagerView`, `ApprovePlan`         | See & approve the roadmap |
| `/agents`   | `AgentCards`, `StatusBadge`, `OutputPreview`, `Logs` | Monitor per-agent state   |
| `/graph`    | `GraphView`, `NodeDetail`, `EdgeInspector`           | Visualize context         |
| `/timeline` | `AgentTimeline`, `LogsTimeline`                      | Full trace of actions     |
| `/reports`  | `ReportViewer`, `FormatSelector`, `ChartDisplay`     | View & download reports   |
| `/settings` | `ApprovalToggles`, `MemoryControls`                  | Configure agent autonomy  |

---

## 🔐 Approval Flow

Set per-agent approval like this (in YAML config or via `/settings`):

```yaml
approval_mode:
  finance_agent:
    api_calls: manual
    memory_write: manual
  marketing_agent:
    api_calls: auto
    memory_write: auto
```

🔔 When manual approval is triggered:

* UI shows modal with: tool name, agent name, input/output preview
* Four actions available: ✅ **Approve** / ❌ **Deny** / 📝 **Edit** / 🔁 **Retry**

---

## 🔀 Execution Flow

```plaintext
1. USER submits vision → /start
2. COFOUNDER agent → captures and stores it
3. MANAGER agent → builds roadmap + assigns work
4. SPECIALIST agents trigger in parallel
   - Each one reads vision, tasks, and peer context
5. If approval is needed → modal appears
6. When all are done:
   - Context saved to graph
   - Exports written to disk
   - UI notifies completion
```

---

## 📁 File Structure (Final)

```
agentflow/
├── frontend/            # React + Vite UI
│   ├── pages/
│   ├── components/
│   └── lib/api.ts
├── backend/             # FastAPI, LangGraph, LangChain
│   ├── agents/
│   ├── flows/
│   ├── memory/
│   ├── tools/
│   └── approvals/
├── data/                # Outputs like vision.json, plan.yml, etc.
├── graph.db/            # Neo4j dump or live socket
├── vector.db/           # Qdrant state
├── docker-compose.yml
├── README.md
```

---

## 📄 Deliverables (Generated by Agents)

The system generates a suite of professional reports in various formats, moving beyond simple data dumps to provide actionable, company-ready documents.

| Report Type                 | Format(s)                      | Source Agent(s)      | Description                                                 |
|:----------------------------|:-------------------------------|:---------------------|:------------------------------------------------------------|
| **Executive Summary**       | `PDF`, `HTML`                  | Manager, All         | A high-level overview of the project, health, and key metrics. |
| **Financial Report**        | `PDF` (with charts), `CSV`     | Finance              | Detailed financial projections, ROI analysis, and budget with Seaborn charts. |
| **Marketing & Content Plan**| `Markdown`, `HTML` (blog post) | Marketing            | A full content strategy, SEO keywords, and sample blog posts. |
| **Sales Forecast**          | `CSV`, `JSON`                  | Sales                | Quarterly sales projections, target customer segments, and pipeline data. |
| **Legal & Compliance Pack** | `PDF`                          | Legal                | Generated ToS, Privacy Policy, and a full compliance audit report. |
| **Product Roadmap**         | `YAML`, `PNG` (Gantt)          | Product, Manager     | The detailed product plan and a visual Gantt chart of the timeline. |
| **Raw Agent Outputs**       | `YAML`                         | All Specialists      | The original, raw structured data from each specialist agent. |
| **Full Memory Graph**       | `graph.graphml`                | All Agents           | A complete, explorable export of the Neo4j memory graph.      |
| **Execution Timeline**      | `JSON`                         | Backend              | A raw event log of every action, decision, and tool call.     |

---

## 🧾 Final Summary (Paste to Windsurf)

```txt
Build a fullstack virtual AI office platform called `agentflow`. It includes async agents with defined roles (Cofounder, Manager, Product, Finance, Marketing, Legal) that collaborate through LangGraph and use tools like Crawl4AI, OpenRouter, Qdrant, and Graphiti (Neo4j) for memory and coordination.

Each agent has:
- A personality (prompt style, retry logic)
- A private memory space in Neo4j
- Access to a global shared context (Graph DB)
- Tools to query APIs, fetch data, or generate content

Agents coordinate in parallel via a LangGraph DAG. A human user monitors progress via a UI (React + Vite), views every memory/action, and approves/dismisses API/memory calls per agent.

The backend (FastAPI) supports endpoint triggers, approval middleware, and data exports. All agent outputs are written to `/data/*.json` or `.yml`.

The UI includes:
- /start
- /vision
- /agents
- /graph
- /timeline
- /outputs
- /settings

All configuration, memory state, and tool usage is transparent and traceable.
```

---






# 🧩 Final UI/UX Workflow for `agentflow` (Virtual AI Office)

---

## 🖥️ App Overview: Interface Zones

| Zone                     | Description                                                                           |
| ------------------------ | ------------------------------------------------------------------------------------- |
| **Sidebar (Global Nav)** | Switch between: `Dashboard`, `Agents`, `Vision`, `Plan`, `Graph`, `Settings`, `Legal` |
| **Main Canvas**          | Displays real-time state: agent outputs, logs, current flow, pending actions          |
| **Inspector Panel**      | Drill-down for selected agent, memory node, or context object                         |
| **Approval Modal**       | Appears whenever human approval is needed (API call, memory write, plan change)       |
| **Graph Overlay**        | Interactive view of shared memory graph (Neo4j/Graphiti-powered)                      |

---

## 👨‍💼 Primary User Roles

| Role                      | Rights                             |
| ------------------------- | ---------------------------------- |
| **Owner (you)**           | Full visibility + approval control |
| **Viewer (guest/future)** | Read-only mode                     |

---

## 🧠 UX: Human-in-the-Loop Flow

### 1. 📌 Start: Launch New Project

* Page: `/start`
* Inputs: Name, project idea, user type, initial vision
* Triggers **Cofounder Agent**

---

### 2. 🧠 Planning View: `/vision`

* Renders: Output from Cofounder + Manager
* Display:

  * Project vision (editable)
  * Agent-generated roadmap (view + approve)
* User Actions:

  * ✅ Approve plan → triggers agentflow
  * ✏️ Edit plan → re-triggers `Manager Agent`

---

### 3. 🧩 Agent Panel: `/agents`

Shows **each agent's lifecycle status**:

| Agent     | Status    | Actions             |
| --------- | --------- | ------------------- |
| Cofounder | ✅ done    | 🧠 view             |
| Manager   | ✅ done    | 🧠 view             |
| Product   | ⏳ running | 🛑 stop / 📤 export |
| Finance   | 🔁 retry  | 🧠 logs             |
| Marketing | ⏸ paused  | ▶️ resume           |

**Clicking an agent** opens:

* Memory nodes it has written
* Decisions it made
* API calls (manual approval if enabled)

---

### 4. 🔍 Graph View: `/graph`

* Shows current shared context in Neo4j/Graphiti style
* Node types: `vision`, `feature`, `budget`, `persona`, `campaign`
* Edges: `influences`, `depends_on`, `contradicts`, `derived_from`
* Can be filtered by agent, date, or node type

---

### 5. 🔒 Approval Settings: `/settings`

Controls per-agent automation:

```yaml
approval_mode:
  finance_agent:
    api_calls: "manual"
    memory_write: "auto"
  marketing_agent:
    api_calls: "auto"
    memory_write: "manual"
```

Each approval appears as a modal:

```
🚨 Agent: Finance
🔍 Wants to fetch: /api/balance-sheet?id=demo
✅ Approve / ❌ Deny / 📝 Edit / 🔁 Simulate offline
```

---

### 6. 📊 Output Center: `/outputs`

Aggregates:

* `plan.yml`
* `vision.json`
* `product.json`, `finance.json`, etc.
* One-click export to:

  * `.zip folder`
  * `README.md generator`
  * `mcp.yaml`

---

### 7. ⚙️ Workflow Timeline: `/timeline`

Think: GitHub Actions for Agents

* Each row: timestamp, agent, action, outcome
* Example:

  ```
  [09:32] Cofounder → Parsed user vision
  [09:34] Manager → Created task map
  [09:35] Finance → Called /api/mock-costs [APPROVED]
  [09:36] Marketing → Denied push to shared graph (incomplete inputs)
  ```

---

## 🔁 Interrupts & Control Features

| Feature               | Behavior                                       |
| --------------------- | ---------------------------------------------- |
| **⏸ Pause Agent**     | Freezes the agent and blocks writes/reads      |
| **🔁 Retry Agent**    | Reruns last task, preserving memory            |
| **🛑 Kill Agent**     | Hard stop, deletes transient memory            |
| **✅ Approve Modal**   | Inline blocking UI for sensitive ops           |
| **📝 Inject Message** | User can "say something" mid-flow to any agent |
| **🧠 Context Replay** | Step-by-step memory update playback            |

---

## 🪄 Visual Aesthetic

| Trait                   | UX Choice                                             |
| ----------------------- | ----------------------------------------------------- |
| **Minimalist Dev Tool** | Use a neutral gray/white dark theme                   |
| **Visual Graphs**       | Integrate Graphiti or Neo4j desktop preview           |
| **Modular Sidebar**     | Use Tailwind + Headless UI tabs                       |
| **Reactivity**          | Framer Motion or TanStack animations for agent events |
| **Auto-scroll**         | Message history scrolls with agent outputs            |
| **Toast Feedback**      | Sonner for success/error/hint popups                  |

---

## ✅ TL;DR – User Workflow Summary

```plaintext
1. Launch project → Cofounder clarifies
2. Review roadmap → Manager assembles workstreams
3. Approve roadmap → agents start in parallel
4. View each agent’s live output, logs, and graph impact
5. Approve or deny:
   - API calls
   - Memory write
   - Planning changes
6. Monitor agent flow via Timeline or Graph View
7. Export deliverables (plan, roadmap, legal, marketing)
```

---
