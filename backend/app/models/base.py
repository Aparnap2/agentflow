from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from uuid import uuid4

class UserRole(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"

class AgentRole(str, Enum):
    # Core Roles
    COFOUNDER = "cofounder"
    MANAGER = "manager"

    # Specialist SMB Roles
    CRM_AGENT = "crm_agent"
    EMAIL_MARKETING_AGENT = "email_marketing_agent"
    INVOICE_AGENT = "invoice_agent"
    SCHEDULING_AGENT = "scheduling_agent"
    SOCIAL_MEDIA_AGENT = "social_media_agent"
    HR_AGENT = "hr_agent"
    ADMIN_AGENT = "admin_agent"
    REVIEW_AGENT = "review_agent"

    # Other existing roles (can be reviewed later)
    LEGAL_AGENT = "legal_agent"
    FINANCE_AGENT = "finance_agent" # Note: Different from INVOICE_AGENT
    HEALTHCARE_AGENT = "healthcare_agent"
    MANUFACTURING_AGENT = "manufacturing_agent"
    ECOMMERCE_AGENT = "ecommerce_agent"
    COACHING_AGENT = "coaching_agent"
    SALES = "sales" # Generic sales, CRM_AGENT is more specific
    SUPPORT = "support" # Generic support, REVIEW_AGENT could be part of this
    GROWTH = "growth"

class Department(str, Enum):
    LEADERSHIP = "leadership" # CoFounder, Manager
    OPERATIONS = "operations" # Scheduling_Agent, Admin_Agent
    SALES = "sales" # CRM_Agent (can also be Marketing)
    MARKETING = "marketing" # Email_Marketing_Agent, Social_Media_Agent, Review_Agent
    FINANCE = "finance" # Invoice_Agent
    HR = "hr" # HR_Agent
    SUPPORT = "support" # Review_Agent can also be support
    # Adding a general department for specialists if precise mapping is complex initially
    SPECIALIST = "specialist"

class MessageType(str, Enum):
    HUMAN = "human"
    AI = "ai"
    SYSTEM = "system"
    TOOL = "tool"
