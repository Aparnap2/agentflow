from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional, Dict, Any
import json
import asyncio

from ..models import agent, auth
from ..services.auth_service import AuthService
from ..db.database import DatabaseService

router = APIRouter()
security = HTTPBearer()

def get_db() -> DatabaseService:
    return DatabaseService()

def get_auth_service() -> AuthService:
    return AuthService()

@router.get("/", response_model=List[agent.AgentConfig])
async def list_agents(
    role: Optional[agent.AgentRole] = None,
    department: Optional[agent.Department] = None,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service),
    db: DatabaseService = Depends(get_db)
):
    """List available agents with optional filtering"""
    try:
        # Authenticate user
        current_user = await auth_service.verify_token(credentials.credentials)
        
        # In a real implementation, fetch agents from database with filters
        # This is a simplified example
        query = "SELECT * FROM agents WHERE is_active = true"
        params = []
        
        if role:
            query += " AND role = $1"
            params.append(role.value)
            
        if department:
            query += f" AND {' AND '.join([f'department = ${i+2}' for i, d in enumerate([department])])}"
            params.extend([d.value for d in [department]])
            
        agents = await db.fetch(query, *params)
        return [dict(agent) for agent in agents]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching agents: {str(e)}"
        )

@router.get("/{agent_id}", response_model=agent.AgentConfig)
async def get_agent(
    agent_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service),
    db: DatabaseService = Depends(get_db)
):
    """Get agent by ID"""
    try:
        # Authenticate user
        current_user = await auth_service.verify_token(credentials.credentials)
        
        # Get agent from database
        agent_data = await db.fetchrow(
            "SELECT * FROM agents WHERE agent_id = $1 AND is_active = true",
            agent_id
        )
        
        if not agent_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found"
            )
            
        return dict(agent_data)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching agent: {str(e)}"
        )

@router.websocket("/ws/{agent_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    agent_id: str,
    token: str
):
    """WebSocket endpoint for agent communication"""
    try:
        # Authenticate user
        auth_service = AuthService()
        try:
            user = await auth_service.verify_token(token)
        except Exception as e:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
            
        await websocket.accept()
        
        # In a real implementation, you would register this connection
        # with a connection manager and handle bi-directional communication
        
        try:
            while True:
                data = await websocket.receive_text()
                # Process incoming message
                message = json.loads(data)
                
                # Echo back for now
                await websocket.send_json({
                    "type": "response",
                    "content": f"Received: {message}"
                })
                
        except WebSocketDisconnect:
            # Handle disconnection
            pass
            
    except Exception as e:
        # Log the error
        print(f"WebSocket error: {str(e)}")
        try:
            await websocket.close()
        except:
            pass

@router.post("/{agent_id}/invoke", response_model=Dict[str, Any])
async def invoke_agent(
    agent_id: str,
    input_data: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service),
    db: DatabaseService = Depends(get_db)
):
    """Invoke an agent with input data"""
    try:
        # Authenticate user
        current_user = await auth_service.verify_token(credentials.credentials)
        
        # Get agent configuration
        agent_config = await db.fetchrow(
            "SELECT * FROM agents WHERE agent_id = $1 AND is_active = true",
            agent_id
        )
        
        if not agent_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found"
            )
        
        # In a real implementation, you would invoke the agent's logic here
        # This is a simplified example
        response = {
            "agent_id": agent_id,
            "status": "success",
            "result": f"Processed input: {input_data}",
            "metadata": {
                "agent_name": agent_config.get('name', 'Unknown'),
                "role": agent_config.get('role'),
                "timestamp": str(datetime.utcnow())
            }
        }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error invoking agent: {str(e)}"
        )

# Static definitions for the fixed team
# In a real scenario, these would be fetched from a DB and configured
# For now, they are hardcoded to align with the "Virtual Office" concept

# Generate fixed UUIDs for consistent referencing if needed, especially for manager_id
from uuid import UUID

cofounder_id = str(UUID("00000000-0000-0000-0000-000000000001"))
manager_id = str(UUID("00000000-0000-0000-0000-000000000002"))

fixed_team_agents_data = [
    {
        "id": cofounder_id,
        "name": "Co-Founder Agent",
        "role": agent.AgentRole.COFOUNDER,
        "department": agent.Department.LEADERSHIP,
        "level": 1,
        "tools": ["StrategicPlannerTool", "GoalSettingTool"],
        "specializations": ["Business Strategy", "Product Vision", "Team Leadership", "Intent Analysis"],
        "system_prompt": "You are the Co-Founder agent, responsible for translating business goals into actionable strategies and objectives for the AI team. Analyze user intent and set the overall direction.",
        "is_active": True,
        "max_concurrent_tasks": 1, # Typically handles one major intent at a time
    },
    {
        "id": manager_id,
        "name": "Manager Agent",
        "role": agent.AgentRole.MANAGER,
        "department": agent.Department.LEADERSHIP,
        "level": 2,
        "manager_id": cofounder_id,
        "tools": ["LangGraphOrchestrator", "TaskAssignerTool", "ProgressMonitorTool"],
        "specializations": ["Project Management", "Team Coordination", "Process Optimization", "Workflow Orchestration", "Agent Handoff"],
        "system_prompt": "You are the Manager agent, responsible for orchestrating specialist agents using LangGraph, managing workflows, decomposing tasks, and ensuring objectives set by the Co-Founder are met efficiently.",
        "is_active": True,
        "max_concurrent_tasks": 5, # Manages multiple specialist agent tasks
    },
    {
        "id": str(UUID("00000000-0000-0000-0000-000000000003")),
        "name": "CRM Agent",
        "role": agent.AgentRole.CRM_AGENT,
        "department": agent.Department.SALES,
        "level": 3,
        "manager_id": manager_id,
        "tools": ["HubSpotAPI", "SalesforceAPI", "GmailAPI", "CalendarAPI"],
        "specializations": ["Lead Management", "Sales Pipeline Automation", "Customer Segmentation", "Follow-up Automation"],
        "system_prompt": "You are the CRM Agent, specializing in automating lead capture, follow-ups, customer segmentation, and sales pipeline updates.",
        "is_active": True,
    },
    {
        "id": str(UUID("00000000-0000-0000-0000-000000000004")),
        "name": "Email Marketing Agent",
        "role": agent.AgentRole.EMAIL_MARKETING_AGENT,
        "department": agent.Department.MARKETING,
        "level": 3,
        "manager_id": manager_id,
        "tools": ["MailchimpAPI", "SendGridAPI", "GmailAPI", "AnalyticsReader"],
        "specializations": ["Email Campaign Management", "Drip Sequences", "Abandoned Cart Recovery", "Newsletter Automation"],
        "system_prompt": "You are the Email Marketing Agent, specializing in handling email campaigns, drip sequences, and abandoned cart reminders.",
        "is_active": True,
    },
    {
        "id": str(UUID("00000000-0000-0000-0000-000000000005")),
        "name": "Invoice Agent",
        "role": agent.AgentRole.INVOICE_AGENT,
        "department": agent.Department.FINANCE,
        "level": 3,
        "manager_id": manager_id,
        "tools": ["QuickBooksAPI", "StripeAPI", "PayPalAPI", "PDFGenerator"],
        "specializations": ["Invoice Automation", "Payment Reminders", "Reconciliation Support", "Expense Tracking"],
        "system_prompt": "You are the Invoice Agent, specializing in automating invoice creation, sending, payment reminders, and reconciliation.",
        "is_active": True,
    },
    {
        "id": str(UUID("00000000-0000-0000-0000-000000000006")),
        "name": "Scheduling Agent",
        "role": agent.AgentRole.SCHEDULING_AGENT,
        "department": agent.Department.OPERATIONS,
        "level": 3,
        "manager_id": manager_id,
        "tools": ["GoogleCalendarAPI", "CalendlyAPI", "ZoomAPI"],
        "specializations": ["Appointment Booking Automation", "Calendar Synchronization", "Meeting Reminders", "Availability Management"],
        "system_prompt": "You are the Scheduling Agent, specializing in managing appointment bookings, reminders, and calendar synchronization.",
        "is_active": True,
    },
    {
        "id": str(UUID("00000000-0000-0000-0000-000000000007")),
        "name": "Social Media Agent",
        "role": agent.AgentRole.SOCIAL_MEDIA_AGENT,
        "department": agent.Department.MARKETING,
        "level": 3,
        "manager_id": manager_id,
        "tools": ["TwitterAPI", "LinkedInAPI", "FacebookAPI", "HootsuiteAPI"],
        "specializations": ["Social Media Posting Automation", "Engagement Monitoring", "Content Scheduling", "Basic Reporting"],
        "system_prompt": "You are the Social Media Agent, specializing in scheduling and posting to social media, monitoring engagement, and basic reporting.",
        "is_active": True,
    },
    {
        "id": str(UUID("00000000-0000-0000-0000-000000000008")),
        "name": "HR Agent",
        "role": agent.AgentRole.HR_AGENT,
        "department": agent.Department.HR,
        "level": 3,
        "manager_id": manager_id,
        "tools": ["BambooHRAPI", "SlackAPI", "GoogleSheetsAPI", "SurveyMonkeyAPI"],
        "specializations": ["Time Tracking Support", "Leave Request Management", "Onboarding Automation", "Payroll Notifications"],
        "system_prompt": "You are the HR Agent, specializing in tasks like time tracking, managing leave requests, and onboarding notifications.",
        "is_active": True,
    },
    {
        "id": str(UUID("00000000-0000-0000-0000-000000000009")),
        "name": "Admin Agent",
        "role": agent.AgentRole.ADMIN_AGENT,
        "department": agent.Department.OPERATIONS,
        "level": 3,
        "manager_id": manager_id,
        "tools": ["GoogleFormsAPI", "AirtableAPI", "NotionAPI", "PDFGeneratorTool", "DataEntryTool"],
        "specializations": ["Form Filling Automation", "Routine Data Collection", "Simple Report Generation", "Document Workflow Management"],
        "system_prompt": "You are the Admin Agent, specializing in filling out forms, collecting routine data, generating simple reports, and managing document workflows.",
        "is_active": True,
    },
    {
        "id": str(UUID("00000000-0000-0000-0000-000000000010")), # Corrected ID to be unique
        "name": "Review Agent",
        "role": agent.AgentRole.REVIEW_AGENT,
        "department": agent.Department.MARKETING, # Or SUPPORT
        "level": 3,
        "manager_id": manager_id,
        "tools": ["GoogleReviewsAPI", "YelpAPI", "TrustpilotAPI", "SentimentAnalysisTool"],
        "specializations": ["Customer Review Monitoring", "Automated Feedback Requests", "Sentiment Summaries", "Response Drafting"],
        "system_prompt": "You are the Review Agent, specializing in monitoring and responding to customer reviews, sending automated feedback requests, and compiling sentiment summaries.",
        "is_active": True,
    }
]

# Convert list of dicts to list of AgentConfig models
# We need to ensure all fields are present or have defaults in AgentConfig model
team_definitions = [agent.AgentConfig(**data) for data in fixed_team_agents_data]

@router.get("/team-definition", response_model=List[agent.AgentConfig])
async def get_team_definition():
    """
    Provides the definition of the fixed virtual office team.
    This is a temporary endpoint and will be replaced by dynamic fetching
    from a database or configuration once auth and DB seeding are in place.
    """
    return team_definitions

# To make the original /agents endpoint unauthenticated for now (TEMPORARY for easier dev)
# Comment out or remove `credentials: HTTPAuthorizationCredentials = Depends(security)`
# and the `auth_service.verify_token` call.
# This is NOT recommended for production.
# For now, I will leave it as is, and the new /team-definition endpoint will be used by the UI.
