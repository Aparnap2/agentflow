// Corresponds to backend/app/models/base.py
export enum AgentRole {
  // Core Roles
  COFOUNDER = "cofounder",
  MANAGER = "manager",

  // Specialist SMB Roles
  CRM_AGENT = "crm_agent",
  EMAIL_MARKETING_AGENT = "email_marketing_agent",
  INVOICE_AGENT = "invoice_agent",
  SCHEDULING_AGENT = "scheduling_agent",
  SOCIAL_MEDIA_AGENT = "social_media_agent",
  HR_AGENT = "hr_agent",
  ADMIN_AGENT = "admin_agent",
  REVIEW_AGENT = "review_agent",

  // Other existing roles (can be reviewed later)
  LEGAL_AGENT = "legal_agent",
  FINANCE_AGENT = "finance_agent",
  HEALTHCARE_AGENT = "healthcare_agent",
  MANUFACTURING_AGENT = "manufacturing_agent",
  ECOMMERCE_AGENT = "ecommerce_agent",
  COACHING_AGENT = "coaching_agent",
  SALES = "sales",
  SUPPORT = "support",
  GROWTH = "growth",
}

export enum Department {
  LEADERSHIP = "leadership",
  OPERATIONS = "operations",
  SALES = "sales",
  MARKETING = "marketing",
  FINANCE = "finance",
  HR = "hr",
  SUPPORT = "support",
  SPECIALIST = "specialist",
}

// Corresponds to backend/app/models/agent.py AgentConfig
export interface AgentConfig {
  id: string;
  name: string;
  role: AgentRole;
  department: Department;
  level: number;
  manager_id?: string | null; // Optional in Pydantic
  direct_reports: string[]; // Pydantic default_factory=list
  tools: string[]; // Pydantic default_factory=list
  specializations: string[]; // Pydantic default_factory=list
  system_prompt: string; // Pydantic default=""
  max_concurrent_tasks: number; // Pydantic default=5
  is_active: boolean; // Pydantic default=True
  created_at: string; // Pydantic default_factory=datetime.now -> will be ISO string
  performance_metrics: Record<string, any>; // Pydantic default_factory=dict
  memory_context: Record<string, any>; // Pydantic default_factory=dict
}
