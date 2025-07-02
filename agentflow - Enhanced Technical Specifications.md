# `agentflow` - Enhanced Technical Specifications

*Based on PRD v1.3 by Aparna Pradhan*

## 🏗️ System Architecture Overview

### Core Components

```
Frontend (React + Vite + Tailwind) 
    ↓ HTTP/WebSocket + Real-time Updates
Backend (FastAPI + Python + Pandas)
    ↓ Agent Orchestration + Approval Middleware
LangGraph Agent Network (7 Specialized Agents)
    ↓ Memory Operations + Tool Execution
Neo4j/Graphiti (Structured) + Qdrant (Semantic)
    ↓ External APIs + Tool Integrations
OpenRouter LLM + Crawl4AI + Reporting Suite
```

### Enhanced Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│ UI Layer: React + Tailwind + Framer Motion                 │
├─────────────────────────────────────────────────────────────┤
│ API Layer: FastAPI + WebSocket + Approval Middleware       │
├─────────────────────────────────────────────────────────────┤
│ Agent Layer: LangGraph DAG + Agent Personalities           │
├─────────────────────────────────────────────────────────────┤
│ Memory Layer: Neo4j (Private + Shared) + Qdrant (Semantic) │
├─────────────────────────────────────────────────────────────┤
│ Tool Layer: OpenRouter + Crawl4AI + Report Generation      │
├─────────────────────────────────────────────────────────────┤
│ Storage Layer: Local Files (YAML/CSV/PDF/HTML/PNG)         │
└─────────────────────────────────────────────────────────────┘
```

## 📊 Enhanced Data Models & Schemas

### 1. Agent Schema (Enhanced)

```python
class Agent:
    id: str
    name: str  # e.g. "Alex Chen", "Sarah Kim"
    role: str  # cofounder, manager, product, finance, marketing, legal, sales
    personality: AgentPersonality
    tools: list[str]  # From PRD toolkits
    memory_context: str
    status: "idle" | "working" | "waiting_approval" | "paused" | "retry" | "done"
    current_task_id: str | None
    confidence_threshold: float = 0.6  # Triggers manual approval if below
    approval_mode: ApprovalConfig
    created_at: datetime
    last_activity: datetime
    private_memory_nodes: list[str]  # Neo4j node IDs
    shared_context_contributions: list[str]
```

### 2. Agent Personality Schema

```python
class AgentPersonality:
    traits: list[str]  # ["visionary", "strategic", "decisive"]
    communication_style: str  # "inspirational", "clear_and_structured"
    decision_making: str  # "big_picture_focused", "consensus_building"
    prompt_template: str  # LangGraph system prompt
    temperature: float = 0.7
    max_tokens: int = 2000
    retry_attempts: int = 3
```

### 3. Approval Configuration Schema

```python
class ApprovalConfig:
    api_calls: "auto" | "manual"
    memory_write: "auto" | "manual" 
    external_communication: "auto" | "manual"
    budget_decisions: "auto" | "manual"
    document_publishing: "auto" | "manual"
```

### 4. Enhanced Memory Schema (Neo4j/Graphiti)

```cypher
// Core Nodes
(:Agent {id, name, role, expertise, personality_hash})
(:Vision {id, content, version, approved_by, timestamp})
(:Task {id, title, status, priority, assigned_agent, confidence_score})
(:Decision {id, content, reasoning, agent_id, approval_status, timestamp})
(:Document {id, title, type, format, content_hash, export_path})
(:Tool {id, name, description, agent_access_list})
(:MemoryNode {id, type, content, private, agent_owner, timestamp})

// Enhanced Relationships
(:Agent)-[:HAS_PRIVATE_MEMORY]->(:MemoryNode)
(:Agent)-[:CONTRIBUTED_TO]->(:SharedContext)
(:Agent)-[:USED_TOOL]->(:Tool)
(:Agent)-[:MADE_DECISION]->(:Decision)
(:Decision)-[:INFLUENCES]->(:Vision)
(:Task)-[:DEPENDS_ON]->(:Task)
(:Task)-[:DERIVED_FROM]->(:Vision)
(:MemoryNode)-[:CONTRADICTS]->(:MemoryNode)
(:Document)-[:GENERATED_BY]->(:Agent)
```

### 5. LangGraph Workflow State

```python
class WorkflowState:
    project_id: str
    current_phase: "planning" | "execution" | "review" | "complete"
    active_agents: list[str]
    shared_context: SharedContextGraph
    pending_approvals: list[ApprovalRequest]
    execution_timeline: list[WorkflowEvent]
    global_memory: dict
    agent_states: dict[str, AgentState]
```

### 6. Tool Integration Schema

```python
class ToolCall:
    tool_name: str
    agent_id: str
    input_params: dict
    output_result: dict
    confidence: float
    requires_approval: bool
    approval_status: "pending" | "approved" | "denied" | "auto"
    timestamp: datetime
    execution_time_ms: int
```

## 🔄 Enhanced Workflow Engine (LangGraph DAG Implementation)

### 1. LangGraph Agent Network Structure

```python
from langgraph.graph import StateGraph, MessagesState
from langgraph.prebuilt import ToolNode

class AgentFlowState(MessagesState):
    project_vision: str
    shared_context: dict
    agent_outputs: dict[str, dict]
    pending_approvals: list[dict]
    workflow_phase: str
    human_feedback: dict

# LangGraph DAG Implementation
def create_agent_workflow():
    workflow = StateGraph(AgentFlowState)
    
    # Sequential Phase
    workflow.add_node("cofounder", cofounder_agent)
    workflow.add_node("manager", manager_agent)
    
    # Parallel Specialist Phase
    workflow.add_node("product", product_agent)
    workflow.add_node("finance", finance_agent) 
    workflow.add_node("marketing", marketing_agent)
    workflow.add_node("legal", legal_agent)
    workflow.add_node("sales", sales_agent)
    
    # Control Nodes
    workflow.add_node("approval_gate", approval_checkpoint)
    workflow.add_node("context_sync", sync_shared_context)
    workflow.add_node("export_outputs", generate_deliverables)
    
    # Conditional Routing
    workflow.add_conditional_edges(
        "cofounder",
        should_continue_to_manager,
        {"continue": "manager", "needs_approval": "approval_gate"}
    )
    
    # Parallel execution after manager
    workflow.add_edge("manager", "product")
    workflow.add_edge("manager", "finance")
    workflow.add_edge("manager", "marketing")
    workflow.add_edge("manager", "legal") 
    workflow.add_edge("manager", "sales")
    
    # Convergence point
    workflow.add_edge(["product", "finance", "marketing", "legal", "sales"], "context_sync")
    workflow.add_edge("context_sync", "export_outputs")
    
    return workflow.compile()
```

### 2. Agent Execution Flow with Approval Gates

```python
class AgentExecutor:
    def __init__(self, agent_config: AgentPersonality):
        self.config = agent_config
        self.approval_required = self._check_approval_requirements()
    
    async def execute_with_approval(self, task: Task, tools: list[Tool]):
        # Pre-execution approval check
        if self.approval_required:
            approval = await self._request_human_approval(task)
            if not approval.approved:
                return self._handle_rejection(approval)
        
        # Execute with confidence monitoring
        result = await self._execute_task(task, tools)
        
        # Post-execution approval for memory writes
        if result.confidence < self.config.confidence_threshold:
            memory_approval = await self._request_memory_approval(result)
            if memory_approval.approved:
                await self._write_to_memory(result)
        else:
            await self._write_to_memory(result)
        
        return result
```

### 3. Tool Integration & Approval System

```python
class ToolExecutor:
    def __init__(self, agent_id: str, approval_config: ApprovalConfig):
        self.agent_id = agent_id
        self.approval_config = approval_config
    
    async def execute_tool(self, tool_name: str, params: dict):
        tool_call = ToolCall(
            tool_name=tool_name,
            agent_id=self.agent_id,
            input_params=params,
            requires_approval=self._needs_approval(tool_name)
        )
        
        if tool_call.requires_approval:
            approval = await self._request_approval(tool_call)
            if not approval.approved:
                return self._create_denied_result(tool_call, approval.reason)
        
        # Execute the actual tool
        start_time = time.time()
        result = await self._execute_tool_function(tool_name, params)
        execution_time = (time.time() - start_time) * 1000
        
        tool_call.output_result = result
        tool_call.execution_time_ms = execution_time
        tool_call.approval_status = "approved" if not tool_call.requires_approval else "approved"
        
        # Log to timeline
        await self._log_tool_execution(tool_call)
        
        return result
```

## 🎭 Enhanced Agent Specifications (Based on PRD)

### 🧠 Cofounder Agent - "Alex Chen"

```yaml
name: "Alex Chen"
personality:
  traits: ["visionary", "strategic", "decisive", "inspirational"]
  communication_style: "conversational"  # Per PRD: conversational vs Legal's strict
  decision_making: "big_picture_focused"
  prompt_template: |
    You are Alex Chen, a visionary cofounder. You think big picture, inspire teams, 
    and translate user ideas into compelling business visions. Be conversational 
    but strategic. Focus on market opportunities and long-term value creation.
  temperature: 0.7
  max_tokens: 2000
  confidence_threshold: 0.6

tools:  # From PRD Toolkit
  - llm_reasoning
  - memory_write
  - memory_query
  - market_research_web
  - vision_articulation

workflows:
  vision_capture:
    - parse_user_input
    - clarify_business_concept  
    - identify_target_users
    - define_value_proposition
    - write_vision_document
    - store_to_shared_context

approval_config:
  api_calls: "auto"
  memory_write: "manual"  # Vision changes need approval
  external_communication: "manual"

memory_focus:
  - project_vision
  - market_insights
  - user_needs
  - business_model
  - success_metrics
```

### 🧭 Manager Agent - "Sarah Kim"

```yaml
name: "Sarah Kim"
personality:
  traits: ["organized", "collaborative", "pragmatic", "systematic"]
  communication_style: "clear_and_structured"
  decision_making: "consensus_building"
  prompt_template: |
    You are Sarah Kim, an experienced project manager. You excel at breaking down 
    complex visions into actionable workstreams, coordinating teams, and ensuring 
    nothing falls through the cracks. Be structured and clear in your communication.
  temperature: 0.3  # Lower for more structured outputs
  confidence_threshold: 0.7

tools:  # From PRD Toolkit
  - memory_read_all
  - task_assign
  - report_compile_all
  - report_export_pdf
  - timeline_planning
  - dependency_analysis

workflows:
  roadmap_creation:
    - read_cofounder_vision
    - decompose_into_workstreams
    - identify_task_dependencies
    - assign_tasks_to_specialists
    - create_project_timeline
    - export_roadmap_plan

approval_config:
  api_calls: "auto"
  memory_write: "auto"
  task_assignment: "manual"  # Task assignments need approval

memory_focus:
  - task_dependencies
  - resource_allocation
  - project_timeline
  - team_coordination
  - progress_tracking
```

### 🎯 Product Agent - "David Rodriguez"

```yaml
name: "David Rodriguez"
personality:
  traits: ["user_focused", "analytical", "innovative", "methodical"]
  communication_style: "data_driven"
  decision_making: "user_centric"
  temperature: 0.5
  confidence_threshold: 0.6

tools:  # From PRD Toolkit
  - rag_search  # Semantic search via Qdrant
  - persona_create
  - plan_export_yaml
  - chart_gantt
  - user_research_web
  - feature_prioritization

workflows:
  product_definition:
    - analyze_vision_requirements
    - create_user_personas
    - define_core_features
    - prioritize_feature_backlog
    - design_mvp_scope
    - generate_product_roadmap
    - export_yaml_plan

approval_config:
  api_calls: "auto"
  memory_write: "auto"
  feature_decisions: "manual"

memory_focus:
  - user_personas
  - feature_requirements
  - product_roadmap
  - mvp_definition
  - user_journey_maps
```

### 💸 Finance Agent - "Maria Lopez"

```yaml
name: "Maria Lopez" 
personality:
  traits: ["analytical", "risk_aware", "detail_oriented", "conservative"]
  communication_style: "fact_based"
  decision_making: "data_driven"
  temperature: 0.2  # Most conservative for financial accuracy
  confidence_threshold: 0.8  # Higher threshold for financial decisions

tools:  # From PRD Toolkit
  - mock_finance_call
  - web_fetch
  - chart_generate_seaborn
  - report_export_csv
  - roi_calculator
  - budget_modeling

workflows:
  financial_planning:
    - fetch_market_data
    - create_budget_model
    - calculate_roi_projections
    - forecast_revenue_streams
    - analyze_cost_structure
    - generate_financial_charts
    - export_financial_report

approval_config:
  api_calls: "manual"  # All financial API calls need approval
  memory_write: "manual"
  budget_decisions: "manual"

memory_focus:
  - budget_allocations
  - revenue_projections
  - cost_analysis
  - roi_calculations
  - financial_milestones
```

### 📣 Marketing Agent - "Jennifer Wu"

```yaml
name: "Jennifer Wu"
personality:
  traits: ["creative", "strategic", "persuasive", "trend_aware"]
  communication_style: "engaging"
  decision_making: "audience_focused"
  temperature: 0.8  # Higher creativity for marketing content
  confidence_threshold: 0.5

tools:  # From PRD Toolkit
  - web_crawl  # Crawl4AI integration
  - content_generate_html
  - seo_analyze
  - content_export_md
  - social_media_planning
  - competitor_analysis

workflows:
  marketing_strategy:
    - crawl_competitor_content
    - analyze_market_trends
    - define_target_audience
    - create_content_strategy
    - plan_seo_optimization
    - generate_blog_content
    - export_marketing_plan

approval_config:
  api_calls: "auto"  # Marketing research is auto-approved
  memory_write: "auto"
  content_publishing: "manual"

memory_focus:
  - content_strategy
  - seo_keywords
  - competitor_insights
  - audience_segments
  - campaign_ideas
```

### ⚖️ Legal Agent - "Robert Johnson"

```yaml
name: "Robert Johnson"
personality:
  traits: ["thorough", "risk_averse", "precise", "compliant"]
  communication_style: "strict"  # Per PRD: Legal is strict vs Cofounder's conversational
  decision_making: "compliance_focused"
  temperature: 0.1  # Most conservative for legal accuracy
  confidence_threshold: 0.9  # Highest threshold for legal decisions

tools:  # From PRD Toolkit
  - compliance_check
  - document_generate_pdf
  - regulatory_validate
  - legal_research_web
  - contract_drafting

workflows:
  legal_compliance:
    - research_regulatory_requirements
    - draft_terms_of_service
    - create_privacy_policy
    - validate_compliance_requirements
    - assess_legal_risks
    - generate_legal_documents
    - export_compliance_pack

approval_config:
  api_calls: "manual"  # All legal research needs approval
  memory_write: "manual"
  document_publishing: "manual"

memory_focus:
  - legal_documents
  - compliance_requirements
  - regulatory_research
  - risk_assessments
  - policy_templates
```

### 📈 Sales Agent - "Michelle Thompson"

```yaml
name: "Michelle Thompson"
personality:
  traits: ["persuasive", "relationship_focused", "results_driven", "optimistic"]
  communication_style: "consultative"
  decision_making: "opportunity_focused"
  temperature: 0.6
  confidence_threshold: 0.6

tools:  # From PRD Toolkit
  - crm_query
  - forecast_generate
  - report_export_csv
  - pipeline_analysis
  - customer_research

workflows:
  sales_strategy:
    - analyze_target_market
    - identify_customer_segments
    - create_sales_funnel
    - develop_pricing_strategy
    - generate_sales_forecast
    - build_pipeline_model
    - export_sales_plan

approval_config:
  api_calls: "auto"
  memory_write: "auto"
  pricing_decisions: "manual"

memory_focus:
  - sales_pipeline
  - customer_segments
  - pricing_strategy
  - revenue_forecasts
  - sales_materials
```

## 🖥️ Frontend Interface Specifications

### 1. Dashboard Layout

```typescript
interface DashboardState {
  activeAgents: Agent[]
  taskQueue: Task[]
  sharedContext: SharedContext
  notifications: Notification[]
  approvalQueue: ApprovalRequest[]
}

components:
  - AgentStatusGrid (7 agent cards)
  - TaskFlowVisualization (Kanban-style)
  - SharedMemoryPanel (context display)
  - ApprovalCenter (human-in-loop)
  - ReportingDashboard (charts/metrics)
```

### 2. Agent Interaction Panel

```typescript
interface AgentPanel {
  agentInfo: Agent
  currentTask: Task | null
  recentActions: Action[]
  memoryInsights: string[]
  toolsAvailable: Tool[]
  communicationLog: Message[]
}
```

### 3. Real-time Updates

```typescript
// WebSocket connection for live updates
useWebSocket('/ws/office-updates', {
  onMessage: (event) => {
    const update = JSON.parse(event.data)
    switch(update.type) {
      case 'agent_status_change':
      case 'task_completed':
      case 'approval_needed':
      case 'memory_updated':
    }
  }
})
```

## 🔧 Backend API Specifications

### 1. Core Endpoints

```python
# Agent Management
POST /api/agents/initialize
GET /api/agents/{agent_id}/status
POST /api/agents/{agent_id}/assign-task
GET /api/agents/{agent_id}/memory

# Task Management  
POST /api/tasks/create
GET /api/tasks/{task_id}
PUT /api/tasks/{task_id}/status
GET /api/tasks/queue

# Memory Operations
GET /api/memory/shared-context
POST /api/memory/update-context
GET /api/memory/search?query={query}

# Approvals
GET /api/approvals/pending
POST /api/approvals/{approval_id}/respond
```

### 2. WebSocket Events

```python
class OfficeWebSocket:
    async def handle_connection(websocket):
        # Real-time updates for:
        # - Agent status changes
        # - Task progress updates
        # - New approvals needed
        # - Memory context changes
        # - Inter-agent communications
```

## 🔄 Inter-Agent Communication Protocol

### 1. Message Structure

```python
class AgentMessage:
    from_agent: str
    to_agent: str | list[str]  # Can broadcast
    message_type: "request" | "response" | "notification" | "question"
    content: str
    context: dict
    requires_response: bool
    priority: "low" | "medium" | "high"
    timestamp: datetime
```

### 2. Communication Patterns

```python
# Direct Communication
cofounder.send_message(
    to="manager",
    message_type="request",
    content="Break down this vision into actionable tasks",
    context={"vision_document": vision_doc}
)

# Broadcast Updates
manager.broadcast_message(
    to=["product", "finance", "marketing"],
    message_type="notification", 
    content="New project timeline established"
)

# Collaborative Decision Making
finance.request_input(
    from_agents=["product", "marketing", "sales"],
    question="What's the priority order for these features based on revenue impact?",
    context={"features": feature_list}
)
```

## 📝 Human-in-the-Loop Approval System

### 1. Approval Types

```python
class ApprovalRequest:
    id: str
    agent_id: str
    task_id: str
    approval_type: "budget_spend" | "external_communication" | "strategic_decision" | "document_publish"
    content: str
    reasoning: str
    impact_assessment: str
    alternatives: list[str]
    deadline: datetime
    
approval_thresholds = {
    "budget_spend": 1000,  # Amounts over $1000
    "external_communication": True,  # All external comms
    "strategic_decision": True,  # Major strategic changes
    "document_publish": ["legal", "marketing"]  # Specific doc types
}
```

### 2. Approval Workflow

```python
async def handle_approval_request(request: ApprovalRequest):
    # Step 1: Queue for human review
    # Step 2: Send notification (email/webhook)
    # Step 3: Wait for human response
    # Step 4: If approved, continue agent execution
    # Step 5: If rejected, return to agent with feedback
    # Step 6: Update shared memory with decision
```

## 📊 Reporting & Analytics System

### 1. Report Types

```python
reports = {
    "executive_summary": {
        "frequency": "weekly",
        "sections": ["progress", "blockers", "decisions", "next_steps"],
        "charts": ["task_completion", "agent_utilization", "budget_burn"]
    },
    "agent_performance": {
        "frequency": "daily", 
        "metrics": ["tasks_completed", "response_time", "approval_rate"],
        "visualizations": ["activity_timeline", "collaboration_network"]
    },
    "project_health": {
        "frequency": "real_time",
        "kpis": ["on_track_percentage", "budget_variance", "timeline_adherence"],
        "alerts": ["blocked_tasks", "overdue_approvals", "budget_overruns"]
    }
}
```

### 2. Chart Generation

```python
class ReportGenerator:
    def generate_task_flow_chart(self, timeframe: str):
        # Seaborn visualization of task completion over time
        
    def create_agent_collaboration_network(self):
        # Network graph of inter-agent communications
        
    def build_budget_burn_chart(self):
        # Financial tracking visualization
        
    def export_pdf_report(self, report_type: str):
        # WeasyPrint PDF generation
```

## 🗄️ File Storage & Output Management

### 1. Output Structure

```
/outputs/
  /reports/
    - executive_summary_{date}.pdf
    - financial_report_{date}.pdf
    - agent_performance_{date}.html
  /documents/
    - terms_of_service.pdf
    - privacy_policy.pdf
    - marketing_plan.html
  /data/
    - project_config.yaml
    - task_history.csv
    - agent_interactions.json
  /visualizations/
    - task_flow_chart.png
    - collaboration_network.png
    - budget_tracking.png
```

### 2. Configuration Management

```yaml
# config/office_config.yaml
project:
  name: "AI Virtual Office Demo"
  phase: "development"
  budget: 50000
  timeline: "6 months"

agents:
  cofounder:
    model: "gemini-pro"
    temperature: 0.7
    max_tokens: 2000
  manager:
    model: "deepseek-coder"
    temperature: 0.3
    max_tokens: 1500
    
memory:
  neo4j:
    uri: "bolt://localhost:7687"
    retention_days: 90
  qdrant:
    collection_name: "office_memory"
    vector_size: 1536
```

## 🚀 Deployment & Development Workflow

### 1. Development Setup

```bash
# Backend Setup
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend Setup  
cd frontend
npm install
npm run dev

# Services Setup
docker-compose up -d  # Neo4j + Qdrant
```

### 2. Environment Variables

```env
# .env
OPENROUTER_API_KEY=your_key_here
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
QDRANT_URL=http://localhost:6333
CRAWL4AI_API_KEY=your_key_here
```

### 3. Testing Strategy

```python
# Unit Tests
test_agent_initialization()
test_task_assignment()
test_memory_operations()
test_approval_workflow()

# Integration Tests  
test_end_to_end_workflow()
test_agent_collaboration()
test_human_approval_flow()

# Performance Tests
test_concurrent_agent_execution()
test_memory_retrieval_speed()
test_report_generation_time()
```

## 📋 Implementation Checklist

### Phase 1: Core Infrastructure (Week 1-2)

- [ ] FastAPI backend with basic endpoints
- [ ] React frontend with dashboard layout
- [ ] Neo4j and Qdrant integration
- [ ] Basic agent initialization
- [ ] Simple task queue system

### Phase 2: Agent Implementation (Week 3-4)

- [ ] LangGraph agent network setup
- [ ] Individual agent personalities and tools
- [ ] Inter-agent communication protocol
- [ ] Shared memory management
- [ ] Basic workflow execution

### Phase 3: Human Integration (Week 5-6)

- [ ] Approval system implementation
- [ ] Real-time WebSocket updates
- [ ] Notification system
- [ ] Human feedback integration
- [ ] Error handling and recovery

### Phase 4: Reporting & Polish (Week 7-8)

- [ ] Report generation system
- [ ] Data visualization charts
- [ ] PDF export functionality
- [ ] Performance optimization
- [ ] Documentation and demos

This specification provides a complete blueprint for your AI Virtual Office project. Each component is detailed enough for implementation while maintaining the flexibility needed for a portfolio showcase.







## 🖥️ Enhanced Frontend Interface (Based on PRD UI/UX)

### 1. Route Structure & Components

```typescript
// Route Mapping from PRD
const routes = {
  '/start': 'ProjectInitiation',
  '/vision': 'VisionReview', 
  '/agents': 'AgentDashboard',
  '/graph': 'MemoryGraphView',
  '/timeline': 'ExecutionTimeline',
  '/outputs': 'ReportCenter',
  '/settings': 'ApprovalSettings'
}

interface AppState {
  project: Project
  agents: Agent[]
  sharedContext: SharedContextGraph
  approvalQueue: ApprovalRequest[]
  workflowState: WorkflowState
  notifications: Notification[]
}
```

### 2. Enhanced Agent Dashboard (`/agents`)

```typescript
interface AgentDashboard {
  agents: AgentCard[]
  statusGrid: AgentStatusGrid
  taskFlow: KanbanBoard
  approvalCenter: ApprovalModal
  inspectorPanel: AgentInspector
}

interface AgentCard {
  agent: Agent
  status: "✅ done" | "⏳ running" | "🔁 retry" | "⏸ paused" | "🛑 stopped"
  currentTask: Task | null
  lastAction: string
  memoryNodes: MemoryNode[]
  actions: ["🧠 view", "📤 export", "🛑 stop", "▶️ resume", "🔁 retry"]
}

// Real-time status updates
const useAgentStatus = (agentId: string) => {
  const [status, setStatus] = useState<AgentStatus>()
  
  useWebSocket(`/ws/agent/${agentId}`, {
    onMessage: (event) => {
      const update = JSON.parse(event.data)
      setStatus(update.status)
      
      // Handle different update types
      switch(update.type) {
        case 'status_change':
          showNotification(`${update.agent_name} is now ${update.status}`)
        case 'task_completed':
          showNotification(`${update.agent_name} completed: ${update.task_title}`)
        case 'approval_needed':
          showApprovalModal(update.approval_request)
        case 'confidence_low':
          showConfidenceWarning(update.confidence_score)
      }
    }
  })
  
  return status
}
```

### 3. Vision Review Interface (`/vision`)

```typescript
interface VisionReview {
  vision# `agentflow` - Enhanced Technical Specifications
*Based on PRD v1.3 by Aparna Pradhan*

## 🏗️ System Architecture Overview

### Core Components
```

Frontend (React + Vite + Tailwind) ↓ HTTP/WebSocket + Real-time Updates Backend (FastAPI + Python + Pandas) ↓ Agent Orchestration + Approval Middleware LangGraph Agent Network (7 Specialized Agents) ↓ Memory Operations + Tool Execution Neo4j/Graphiti (Structured) + Qdrant (Semantic) ↓ External APIs + Tool Integrations OpenRouter LLM + Crawl4AI + Reporting Suite

```
### Enhanced Architecture Layers
```

┌─────────────────────────────────────────────────────────────┐ │ UI Layer: React + Tailwind + Framer Motion                 │ ├─────────────────────────────────────────────────────────────┤ │ API Layer: FastAPI + WebSocket + Approval Middleware       │ ├─────────────────────────────────────────────────────────────┤ │ Agent Layer: LangGraph DAG + Agent Personalities           │ ├─────────────────────────────────────────────────────────────┤ │ Memory Layer: Neo4j (Private + Shared) + Qdrant (Semantic) │ ├─────────────────────────────────────────────────────────────┤ │ Tool Layer: OpenRouter + Crawl4AI + Report Generation      │ ├─────────────────────────────────────────────────────────────┤ │ Storage Layer: Local Files (YAML/CSV/PDF/HTML/PNG)         │ └─────────────────────────────────────────────────────────────┘

```
## 📊 Enhanced Data Models & Schemas

### 1. Agent Schema (Enhanced)
```python
class Agent:
    id: str
    name: str  # e.g. "Alex Chen", "Sarah Kim"
    role: str  # cofounder, manager, product, finance, marketing, legal, sales
    personality: AgentPersonality
    tools: list[str]  # From PRD toolkits
    memory_context: str
    status: "idle" | "working" | "waiting_approval" | "paused" | "retry" | "done"
    current_task_id: str | None
    confidence_threshold: float = 0.6  # Triggers manual approval if below
    approval_mode: ApprovalConfig
    created_at: datetime
    last_activity: datetime
    private_memory_nodes: list[str]  # Neo4j node IDs
    shared_context_contributions: list[str]
```

### 2. Agent Personality Schema

```python
class AgentPersonality:
    traits: list[str]  # ["visionary", "strategic", "decisive"]
    communication_style: str  # "inspirational", "clear_and_structured"
    decision_making: str  # "big_picture_focused", "consensus_building"
    prompt_template: str  # LangGraph system prompt
    temperature: float = 0.7
    max_tokens: int = 2000
    retry_attempts: int = 3
```

### 3. Approval Configuration Schema

```python
class ApprovalConfig:
    api_calls: "auto" | "manual"
    memory_write: "auto" | "manual" 
    external_communication: "auto" | "manual"
    budget_decisions: "auto" | "manual"
    document_publishing: "auto" | "manual"
```

### 4. Enhanced Memory Schema (Neo4j/Graphiti)

```cypher
// Core Nodes
(:Agent {id, name, role, expertise, personality_hash})
(:Vision {id, content, version, approved_by, timestamp})
(:Task {id, title, status, priority, assigned_agent, confidence_score})
(:Decision {id, content, reasoning, agent_id, approval_status, timestamp})
(:Document {id, title, type, format, content_hash, export_path})
(:Tool {id, name, description, agent_access_list})
(:MemoryNode {id, type, content, private, agent_owner, timestamp})

// Enhanced Relationships
(:Agent)-[:HAS_PRIVATE_MEMORY]->(:MemoryNode)
(:Agent)-[:CONTRIBUTED_TO]->(:SharedContext)
(:Agent)-[:USED_TOOL]->(:Tool)
(:Agent)-[:MADE_DECISION]->(:Decision)
(:Decision)-[:INFLUENCES]->(:Vision)
(:Task)-[:DEPENDS_ON]->(:Task)
(:Task)-[:DERIVED_FROM]->(:Vision)
(:MemoryNode)-[:CONTRADICTS]->(:MemoryNode)
(:Document)-[:GENERATED_BY]->(:Agent)
```

### 5. LangGraph Workflow State

```python
class WorkflowState:
    project_id: str
    current_phase: "planning" | "execution" | "review" | "complete"
    active_agents: list[str]
    shared_context: SharedContextGraph
    pending_approvals: list[ApprovalRequest]
    execution_timeline: list[WorkflowEvent]
    global_memory: dict
    agent_states: dict[str, AgentState]
```

### 6. Tool Integration Schema

```python
class ToolCall:
    tool_name: str
    agent_id: str
    input_params: dict
    output_result: dict
    confidence: float
    requires_approval: bool
    approval_status: "pending" | "approved" | "denied" | "auto"
    timestamp: datetime
    execution_time_ms: int
```

## 🔄 Enhanced Workflow Engine (LangGraph DAG Implementation)

### 1. LangGraph Agent Network Structure

```python
from langgraph.graph import StateGraph, MessagesState
from langgraph.prebuilt import ToolNode

class AgentFlowState(MessagesState):
    project_vision: str
    shared_context: dict
    agent_outputs: dict[str, dict]
    pending_approvals: list[dict]
    workflow_phase: str
    human_feedback: dict

# LangGraph DAG Implementation
def create_agent_workflow():
    workflow = StateGraph(AgentFlowState)
    
    # Sequential Phase
    workflow.add_node("cofounder", cofounder_agent)
    workflow.add_node("manager", manager_agent)
    
    # Parallel Specialist Phase
    workflow.add_node("product", product_agent)
    workflow.add_node("finance", finance_agent) 
    workflow.add_node("marketing", marketing_agent)
    workflow.add_node("legal", legal_agent)
    workflow.add_node("sales", sales_agent)
    
    # Control Nodes
    workflow.add_node("approval_gate", approval_checkpoint)
    workflow.add_node("context_sync", sync_shared_context)
    workflow.add_node("export_outputs", generate_deliverables)
    
    # Conditional Routing
    workflow.add_conditional_edges(
        "cofounder",
        should_continue_to_manager,
        {"continue": "manager", "needs_approval": "approval_gate"}
    )
    
    # Parallel execution after manager
    workflow.add_edge("manager", "product")
    workflow.add_edge("manager", "finance")
    workflow.add_edge("manager", "marketing")
    workflow.add_edge("manager", "legal") 
    workflow.add_edge("manager", "sales")
    
    # Convergence point
    workflow.add_edge(["product", "finance", "marketing", "legal", "sales"], "context_sync")
    workflow.add_edge("context_sync", "export_outputs")
    
    return workflow.compile()
```

### 2. Agent Execution Flow with Approval Gates

```python
class AgentExecutor:
    def __init__(self, agent_config: AgentPersonality):
        self.config = agent_config
        self.approval_required = self._check_approval_requirements()
    
    async def execute_with_approval(self, task: Task, tools: list[Tool]):
        # Pre-execution approval check
        if self.approval_required:
            approval = await self._request_human_approval(task)
            if not approval.approved:
                return self._handle_rejection(approval)
        
        # Execute with confidence monitoring
        result = await self._execute_task(task, tools)
        
        # Post-execution approval for memory writes
        if result.confidence < self.config.confidence_threshold:
            memory_approval = await self._request_memory_approval(result)
            if memory_approval.approved:
                await self._write_to_memory(result)
        else:
            await self._write_to_memory(result)
        
        return result
```

### 3. Tool Integration & Approval System

```python
class ToolExecutor:
    def __init__(self, agent_id: str, approval_config: ApprovalConfig):
        self.agent_id = agent_id
        self.approval_config = approval_config
    
    async def execute_tool(self, tool_name: str, params: dict):
        tool_call = ToolCall(
            tool_name=tool_name,
            agent_id=self.agent_id,
            input_params=params,
            requires_approval=self._needs_approval(tool_name)
        )
        
        if tool_call.requires_approval:
            approval = await self._request_approval(tool_call)
            if not approval.approved:
                return self._create_denied_result(tool_call, approval.reason)
        
        # Execute the actual tool
        start_time = time.time()
        result = await self._execute_tool_function(tool_name, params)
        execution_time = (time.time() - start_time) * 1000
        
        tool_call.output_result = result
        tool_call.execution_time_ms = execution_time
        tool_call.approval_status = "approved" if not tool_call.requires_approval else "approved"
        
        # Log to timeline
        await self._log_tool_execution(tool_call)
        
        return result
```

## 🎭 Enhanced Agent Specifications (Based on PRD)

### 🧠 Cofounder Agent - "Alex Chen"

```yaml
name: "Alex Chen"
personality:
  traits: ["visionary", "strategic", "decisive", "inspirational"]
  communication_style: "conversational"  # Per PRD: conversational vs Legal's strict
  decision_making: "big_picture_focused"
  prompt_template: |
    You are Alex Chen, a visionary cofounder. You think big picture, inspire teams, 
    and translate user ideas into compelling business visions. Be conversational 
    but strategic. Focus on market opportunities and long-term value creation.
  temperature: 0.7
  max_tokens: 2000
  confidence_threshold: 0.6

tools:  # From PRD Toolkit
  - llm_reasoning
  - memory_write
  - memory_query
  - market_research_web
  - vision_articulation

workflows:
  vision_capture:
    - parse_user_input
    - clarify_business_concept  
    - identify_target_users
    - define_value_proposition
    - write_vision_document
    - store_to_shared_context

approval_config:
  api_calls: "auto"
  memory_write: "manual"  # Vision changes need approval
  external_communication: "manual"

memory_focus:
  - project_vision
  - market_insights
  - user_needs
  - business_model
  - success_metrics
```

### 🧭 Manager Agent - "Sarah Kim"

```yaml
name: "Sarah Kim"
personality:
  traits: ["organized", "collaborative", "pragmatic", "systematic"]
  communication_style: "clear_and_structured"
  decision_making: "consensus_building"
  prompt_template: |
    You are Sarah Kim, an experienced project manager. You excel at breaking down 
    complex visions into actionable workstreams, coordinating teams, and ensuring 
    nothing falls through the cracks. Be structured and clear in your communication.
  temperature: 0.3  # Lower for more structured outputs
  confidence_threshold: 0.7

tools:  # From PRD Toolkit
  - memory_read_all
  - task_assign
  - report_compile_all
  - report_export_pdf
  - timeline_planning
  - dependency_analysis

workflows:
  roadmap_creation:
    - read_cofounder_vision
    - decompose_into_workstreams
    - identify_task_dependencies
    - assign_tasks_to_specialists
    - create_project_timeline
    - export_roadmap_plan

approval_config:
  api_calls: "auto"
  memory_write: "auto"
  task_assignment: "manual"  # Task assignments need approval

memory_focus:
  - task_dependencies
  - resource_allocation
  - project_timeline
  - team_coordination
  - progress_tracking
```

### 🎯 Product Agent - "David Rodriguez"

```yaml
name: "David Rodriguez"
personality:
  traits: ["user_focused", "analytical", "innovative", "methodical"]
  communication_style: "data_driven"
  decision_making: "user_centric"
  temperature: 0.5
  confidence_threshold: 0.6

tools:  # From PRD Toolkit
  - rag_search  # Semantic search via Qdrant
  - persona_create
  - plan_export_yaml
  - chart_gantt
  - user_research_web
  - feature_prioritization

workflows:
  product_definition:
    - analyze_vision_requirements
    - create_user_personas
    - define_core_features
    - prioritize_feature_backlog
    - design_mvp_scope
    - generate_product_roadmap
    - export_yaml_plan

approval_config:
  api_calls: "auto"
  memory_write: "auto"
  feature_decisions: "manual"

memory_focus:
  - user_personas
  - feature_requirements
  - product_roadmap
  - mvp_definition
  - user_journey_maps
```

### 💸 Finance Agent - "Maria Lopez"

```yaml
name: "Maria Lopez" 
personality:
  traits: ["analytical", "risk_aware", "detail_oriented", "conservative"]
  communication_style: "fact_based"
  decision_making: "data_driven"
  temperature: 0.2  # Most conservative for financial accuracy
  confidence_threshold: 0.8  # Higher threshold for financial decisions

tools:  # From PRD Toolkit
  - mock_finance_call
  - web_fetch
  - chart_generate_seaborn
  - report_export_csv
  - roi_calculator
  - budget_modeling

workflows:
  financial_planning:
    - fetch_market_data
    - create_budget_model
    - calculate_roi_projections
    - forecast_revenue_streams
    - analyze_cost_structure
    - generate_financial_charts
    - export_financial_report

approval_config:
  api_calls: "manual"  # All financial API calls need approval
  memory_write: "manual"
  budget_decisions: "manual"

memory_focus:
  - budget_allocations
  - revenue_projections
  - cost_analysis
  - roi_calculations
  - financial_milestones
```

### 📣 Marketing Agent - "Jennifer Wu"

```yaml
name: "Jennifer Wu"
personality:
  traits: ["creative", "strategic", "persuasive", "trend_aware"]
  communication_style: "engaging"
  decision_making: "audience_focused"
  temperature: 0.8  # Higher creativity for marketing content
  confidence_threshold: 0.5

tools:  # From PRD Toolkit
  - web_crawl  # Crawl4AI integration
  - content_generate_html
  - seo_analyze
  - content_export_md
  - social_media_planning
  - competitor_analysis

workflows:
  marketing_strategy:
    - crawl_competitor_content
    - analyze_market_trends
    - define_target_audience
    - create_content_strategy
    - plan_seo_optimization
    - generate_blog_content
    - export_marketing_plan

approval_config:
  api_calls: "auto"  # Marketing research is auto-approved
  memory_write: "auto"
  content_publishing: "manual"

memory_focus:
  - content_strategy
  - seo_keywords
  - competitor_insights
  - audience_segments
  - campaign_ideas
```

### ⚖️ Legal Agent - "Robert Johnson"

```yaml
name: "Robert Johnson"
personality:
  traits: ["thorough", "risk_averse", "precise", "compliant"]
  communication_style: "strict"  # Per PRD: Legal is strict vs Cofounder's conversational
  decision_making: "compliance_focused"
  temperature: 0.1  # Most conservative for legal accuracy
  confidence_threshold: 0.9  # Highest threshold for legal decisions

tools:  # From PRD Toolkit
  - compliance_check
  - document_generate_pdf
  - regulatory_validate
  - legal_research_web
  - contract_drafting

workflows:
  legal_compliance:
    - research_regulatory_requirements
    - draft_terms_of_service
    - create_privacy_policy
    - validate_compliance_requirements
    - assess_legal_risks
    - generate_legal_documents
    - export_compliance_pack

approval_config:
  api_calls: "manual"  # All legal research needs approval
  memory_write: "manual"
  document_publishing: "manual"

memory_focus:
  - legal_documents
  - compliance_requirements
  - regulatory_research
  - risk_assessments
  - policy_templates
```

### 📈 Sales Agent - "Michelle Thompson"

```yaml
name: "Michelle Thompson"
personality:
  traits: ["persuasive", "relationship_focused", "results_driven", "optimistic"]
  communication_style: "consultative"
  decision_making: "opportunity_focused"
  temperature: 0.6
  confidence_threshold: 0.6

tools:  # From PRD Toolkit
  - crm_query
  - forecast_generate
  - report_export_csv
  - pipeline_analysis
  - customer_research

workflows:
  sales_strategy:
    - analyze_target_market
    - identify_customer_segments
    - create_sales_funnel
    - develop_pricing_strategy
    - generate_sales_forecast
    - build_pipeline_model
    - export_sales_plan

approval_config:
  api_calls: "auto"
  memory_write: "auto"
  pricing_decisions: "manual"

memory_focus:
  - sales_pipeline
  - customer_segments
  - pricing_strategy
  - revenue_forecasts
  - sales_materials
```

## 🖥️ Frontend Interface Specifications

### 1. Dashboard Layout

```typescript
interface DashboardState {
  activeAgents: Agent[]
  taskQueue: Task[]
  sharedContext: SharedContext
  notifications: Notification[]
  approvalQueue: ApprovalRequest[]
}

components:
  - AgentStatusGrid (7 agent cards)
  - TaskFlowVisualization (Kanban-style)
  - SharedMemoryPanel (context display)
  - ApprovalCenter (human-in-loop)
  - ReportingDashboard (charts/metrics)
```

### 2. Agent Interaction Panel

```typescript
interface AgentPanel {
  agentInfo: Agent
  currentTask: Task | null
  recentActions: Action[]
  memoryInsights: string[]
  toolsAvailable: Tool[]
  communicationLog: Message[]
}
```

### 3. Real-time Updates

```typescript
// WebSocket connection for live updates
useWebSocket('/ws/office-updates', {
  onMessage: (event) => {
    const update = JSON.parse(event.data)
    switch(update.type) {
      case 'agent_status_change':
      case 'task_completed':
      case 'approval_needed':
      case 'memory_updated':
    }
  }
})
```

## 🔧 Backend API Specifications

### 1. Core Endpoints

```python
# Agent Management
POST /api/agents/initialize
GET /api/agents/{agent_id}/status
POST /api/agents/{agent_id}/assign-task
GET /api/agents/{agent_id}/memory

# Task Management  
POST /api/tasks/create
GET /api/tasks/{task_id}
PUT /api/tasks/{task_id}/status
GET /api/tasks/queue

# Memory Operations
GET /api/memory/shared-context
POST /api/memory/update-context
GET /api/memory/search?query={query}

# Approvals
GET /api/approvals/pending
POST /api/approvals/{approval_id}/respond
```

### 2. WebSocket Events

```python
class OfficeWebSocket:
    async def handle_connection(websocket):
        # Real-time updates for:
        # - Agent status changes
        # - Task progress updates
        # - New approvals needed
        # - Memory context changes
        # - Inter-agent communications
```

## 🔄 Inter-Agent Communication Protocol

### 1. Message Structure

```python
class AgentMessage:
    from_agent: str
    to_agent: str | list[str]  # Can broadcast
    message_type: "request" | "response" | "notification" | "question"
    content: str
    context: dict
    requires_response: bool
    priority: "low" | "medium" | "high"
    timestamp: datetime
```

### 2. Communication Patterns

```python
# Direct Communication
cofounder.send_message(
    to="manager",
    message_type="request",
    content="Break down this vision into actionable tasks",
    context={"vision_document": vision_doc}
)

# Broadcast Updates
manager.broadcast_message(
    to=["product", "finance", "marketing"],
    message_type="notification", 
    content="New project timeline established"
)

# Collaborative Decision Making
finance.request_input(
    from_agents=["product", "marketing", "sales"],
    question="What's the priority order for these features based on revenue impact?",
    context={"features": feature_list}
)
```

## 📝 Human-in-the-Loop Approval System

### 1. Approval Types

```python
class ApprovalRequest:
    id: str
    agent_id: str
    task_id: str
    approval_type: "budget_spend" | "external_communication" | "strategic_decision" | "document_publish"
    content: str
    reasoning: str
    impact_assessment: str
    alternatives: list[str]
    deadline: datetime
    
approval_thresholds = {
    "budget_spend": 1000,  # Amounts over $1000
    "external_communication": True,  # All external comms
    "strategic_decision": True,  # Major strategic changes
    "document_publish": ["legal", "marketing"]  # Specific doc types
}
```

### 2. Approval Workflow

```python
async def handle_approval_request(request: ApprovalRequest):
    # Step 1: Queue for human review
    # Step 2: Send notification (email/webhook)
    # Step 3: Wait for human response
    # Step 4: If approved, continue agent execution
    # Step 5: If rejected, return to agent with feedback
    # Step 6: Update shared memory with decision
```

## 📊 Reporting & Analytics System

### 1. Report Types

```python
reports = {
    "executive_summary": {
        "frequency": "weekly",
        "sections": ["progress", "blockers", "decisions", "next_steps"],
        "charts": ["task_completion", "agent_utilization", "budget_burn"]
    },
    "agent_performance": {
        "frequency": "daily", 
        "metrics": ["tasks_completed", "response_time", "approval_rate"],
        "visualizations": ["activity_timeline", "collaboration_network"]
    },
    "project_health": {
        "frequency": "real_time",
        "kpis": ["on_track_percentage", "budget_variance", "timeline_adherence"],
        "alerts": ["blocked_tasks", "overdue_approvals", "budget_overruns"]
    }
}
```

### 2. Chart Generation

```python
class ReportGenerator:
    def generate_task_flow_chart(self, timeframe: str):
        # Seaborn visualization of task completion over time
        
    def create_agent_collaboration_network(self):
        # Network graph of inter-agent communications
        
    def build_budget_burn_chart(self):
        # Financial tracking visualization
        
    def export_pdf_report(self, report_type: str):
        # WeasyPrint PDF generation
```

## 🗄️ File Storage & Output Management

### 1. Output Structure

```
/outputs/
  /reports/
    - executive_summary_{date}.pdf
    - financial_report_{date}.pdf
    - agent_performance_{date}.html
  /documents/
    - terms_of_service.pdf
    - privacy_policy.pdf
    - marketing_plan.html
  /data/
    - project_config.yaml
    - task_history.csv
    - agent_interactions.json
  /visualizations/
    - task_flow_chart.png
    - collaboration_network.png
    - budget_tracking.png
```

### 2. Configuration Management

```yaml
# config/office_config.yaml
project:
  name: "AI Virtual Office Demo"
  phase: "development"
  budget: 50000
  timeline: "6 months"

agents:
  cofounder:
    model: "gemini-pro"
    temperature: 0.7
    max_tokens: 2000
  manager:
    model: "deepseek-coder"
    temperature: 0.3
    max_tokens: 1500
    
memory:
  neo4j:
    uri: "bolt://localhost:7687"
    retention_days: 90
  qdrant:
    collection_name: "office_memory"
    vector_size: 1536
```

## 🚀 Deployment & Development Workflow

### 1. Development Setup

```bash
# Backend Setup
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend Setup  
cd frontend
npm install
npm run dev

# Services Setup
docker-compose up -d  # Neo4j + Qdrant
```

### 2. Environment Variables

```env
# .env
OPENROUTER_API_KEY=your_key_here
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
QDRANT_URL=http://localhost:6333
CRAWL4AI_API_KEY=your_key_here
```

### 3. Testing Strategy

```python
# Unit Tests
test_agent_initialization()
test_task_assignment()
test_memory_operations()
test_approval_workflow()

# Integration Tests  
test_end_to_end_workflow()
test_agent_collaboration()
test_human_approval_flow()

# Performance Tests
test_concurrent_agent_execution()
test_memory_retrieval_speed()
test_report_generation_time()
```

## 📋 Implementation Checklist

### Phase 1: Core Infrastructure (Week 1-2)

- [ ] FastAPI backend with basic endpoints
- [ ] React frontend with dashboard layout
- [ ] Neo4j and Qdrant integration
- [ ] Basic agent initialization
- [ ] Simple task queue system

### Phase 2: Agent Implementation (Week 3-4)

- [ ] LangGraph agent network setup
- [ ] Individual agent personalities and tools
- [ ] Inter-agent communication protocol
- [ ] Shared memory management
- [ ] Basic workflow execution

### Phase 3: Human Integration (Week 5-6)

- [ ] Approval system implementation
- [ ] Real-time WebSocket updates
- [ ] Notification system
- [ ] Human feedback integration
- [ ] Error handling and recovery

### Phase 4: Reporting & Polish (Week 7-8)

- [ ] Report generation system
- [ ] Data visualization charts
- [ ] PDF export functionality
- [ ] Performance optimization
- [ ] Documentation and demos

This specification provides a complete blueprint for your AI Virtual Office project. Each component is detailed enough for implementation while maintaining the flexibility needed for a portfolio showcase.