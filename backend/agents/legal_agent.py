"""
Legal Agent - Handles compliance checking, terms of service, and privacy policy generation
"""

import asyncio
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from langchain.tools import BaseTool
from langchain.schema import BaseMessage
from .langgraph_base import LangGraphAgent
from tools.web_search import WebSearchTool


class ComplianceCheckerTool(BaseTool):
    """Tool for checking regulatory compliance"""
    name: str = "compliance_checker"
    description: str = "Check compliance requirements for different jurisdictions and industries"
    
    def _run(self, business_type: str, jurisdictions: List[str] = None, data_handling: str = "basic") -> Dict[str, Any]:
        if jurisdictions is None:
            jurisdictions = ["US", "EU"]
            
        compliance_requirements = {
            "US": {
                "federal": [
                    "FTC Act compliance for advertising",
                    "CAN-SPAM Act for email marketing",
                    "COPPA if targeting children under 13",
                    "ADA compliance for accessibility"
                ],
                "state": [
                    "CCPA (California Consumer Privacy Act)",
                    "State data breach notification laws",
                    "Business registration requirements"
                ]
            },
            "EU": {
                "gdpr": [
                    "Lawful basis for data processing",
                    "Data subject rights implementation",
                    "Privacy by design principles",
                    "Data Protection Officer if required",
                    "Cookie consent mechanisms"
                ],
                "other": [
                    "Digital Services Act compliance",
                    "Accessibility requirements (EN 301 549)"
                ]
            }
        }
        
        industry_specific = {
            "fintech": ["PCI DSS", "SOX compliance", "Anti-money laundering"],
            "healthcare": ["HIPAA", "FDA regulations", "Medical device regulations"],
            "education": ["FERPA", "COPPA", "Student privacy requirements"],
            "ecommerce": ["Consumer protection laws", "Return policy requirements", "Tax compliance"]
        }
        
        return {
            "jurisdictions_analyzed": jurisdictions,
            "business_type": business_type,
            "general_requirements": {k: v for k, v in compliance_requirements.items() if k in jurisdictions},
            "industry_requirements": industry_specific.get(business_type.lower(), []),
            "data_handling_level": data_handling,
            "priority_actions": [
                "Implement privacy policy",
                "Create terms of service",
                "Set up cookie consent",
                "Establish data retention policies"
            ],
            "risk_level": "medium",
            "checked_at": datetime.now().isoformat()
        }
    
    async def _arun(self, business_type: str, jurisdictions: List[str] = None, data_handling: str = "basic") -> Dict[str, Any]:
        return self._run(business_type, jurisdictions, data_handling)


class DocumentGeneratorTool(BaseTool):
    """Tool for generating legal document templates"""
    name: str = "document_generator"
    description: str = "Generate legal document templates like ToS, Privacy Policy, etc."
    
    def _run(self, document_type: str, company_info: Dict[str, Any], jurisdiction: str = "US") -> Dict[str, Any]:
        company_name = company_info.get("name", "[Company Name]")
        contact_email = company_info.get("email", "[contact@company.com]")
        website = company_info.get("website", "[www.company.com]")
        
        templates = {
            "terms_of_service": self._generate_tos_template(company_name, contact_email, website),
            "privacy_policy": self._generate_privacy_template(company_name, contact_email, website),
            "cookie_policy": self._generate_cookie_template(company_name, website),
            "data_processing_agreement": self._generate_dpa_template(company_name, contact_email)
        }
        
        return {
            "document_type": document_type,
            "template": templates.get(document_type, {}),
            "jurisdiction": jurisdiction,
            "company_info": company_info,
            "generated_at": datetime.now().isoformat(),
            "disclaimer": "This is a template and should be reviewed by a qualified attorney"
        }
    
    def _generate_tos_template(self, company_name: str, contact_email: str, website: str) -> Dict[str, Any]:
        return {
            "title": f"Terms of Service - {company_name}",
            "sections": {
                "1_acceptance": {
                    "title": "Acceptance of Terms",
                    "content": f"By accessing and using {website}, you accept and agree to be bound by the terms and provision of this agreement."
                },
                "2_services": {
                    "title": "Description of Service",
                    "content": f"{company_name} provides [describe your service]. We reserve the right to modify or discontinue the service at any time."
                },
                "3_user_accounts": {
                    "title": "User Accounts",
                    "content": "You are responsible for maintaining the confidentiality of your account and password and for restricting access to your computer."
                },
                "4_prohibited_uses": {
                    "title": "Prohibited Uses",
                    "content": "You may not use our service for any illegal or unauthorized purpose or to violate any laws in your jurisdiction."
                },
                "5_intellectual_property": {
                    "title": "Intellectual Property Rights",
                    "content": f"The service and its original content, features and functionality are and will remain the exclusive property of {company_name}."
                },
                "6_termination": {
                    "title": "Termination",
                    "content": "We may terminate or suspend your account immediately, without prior notice or liability, for any reason whatsoever."
                },
                "7_limitation_liability": {
                    "title": "Limitation of Liability",
                    "content": f"In no event shall {company_name} be liable for any indirect, incidental, special, consequential, or punitive damages."
                },
                "8_governing_law": {
                    "title": "Governing Law",
                    "content": "These Terms shall be interpreted and governed by the laws of [Your Jurisdiction]."
                },
                "9_contact": {
                    "title": "Contact Information",
                    "content": f"If you have any questions about these Terms, please contact us at {contact_email}."
                }
            },
            "last_updated": datetime.now().strftime("%B %d, %Y"),
            "effective_date": datetime.now().strftime("%B %d, %Y")
        }
    
    def _generate_privacy_template(self, company_name: str, contact_email: str, website: str) -> Dict[str, Any]:
        return {
            "title": f"Privacy Policy - {company_name}",
            "sections": {
                "1_introduction": {
                    "title": "Introduction",
                    "content": f"This Privacy Policy describes how {company_name} collects, uses, and shares your personal information when you use our service."
                },
                "2_information_collection": {
                    "title": "Information We Collect",
                    "content": "We collect information you provide directly to us, information we collect automatically when you use our service, and information from third parties."
                },
                "3_use_of_information": {
                    "title": "How We Use Your Information",
                    "content": "We use the information we collect to provide, maintain, and improve our service, process transactions, and communicate with you."
                },
                "4_information_sharing": {
                    "title": "Information Sharing and Disclosure",
                    "content": "We do not sell, trade, or otherwise transfer your personal information to third parties without your consent, except as described in this policy."
                },
                "5_data_security": {
                    "title": "Data Security",
                    "content": "We implement appropriate technical and organizational measures to protect your personal information against unauthorized access, alteration, disclosure, or destruction."
                },
                "6_data_retention": {
                    "title": "Data Retention",
                    "content": "We retain your personal information for as long as necessary to provide our service and fulfill the purposes outlined in this policy."
                },
                "7_your_rights": {
                    "title": "Your Rights",
                    "content": "You have the right to access, update, or delete your personal information. You may also have additional rights depending on your location."
                },
                "8_cookies": {
                    "title": "Cookies and Tracking Technologies",
                    "content": "We use cookies and similar tracking technologies to collect and use personal information about you."
                },
                "9_changes": {
                    "title": "Changes to This Policy",
                    "content": "We may update this Privacy Policy from time to time. We will notify you of any changes by posting the new policy on this page."
                },
                "10_contact": {
                    "title": "Contact Us",
                    "content": f"If you have any questions about this Privacy Policy, please contact us at {contact_email}."
                }
            },
            "last_updated": datetime.now().strftime("%B %d, %Y"),
            "effective_date": datetime.now().strftime("%B %d, %Y")
        }
    
    def _generate_cookie_template(self, company_name: str, website: str) -> Dict[str, Any]:
        return {
            "title": f"Cookie Policy - {company_name}",
            "sections": {
                "1_what_are_cookies": {
                    "title": "What Are Cookies",
                    "content": "Cookies are small text files that are placed on your computer or mobile device when you visit a website."
                },
                "2_how_we_use_cookies": {
                    "title": "How We Use Cookies",
                    "content": "We use cookies to improve your experience on our website, analyze website traffic, and for marketing purposes."
                },
                "3_types_of_cookies": {
                    "title": "Types of Cookies We Use",
                    "content": {
                        "essential": "Necessary for the website to function properly",
                        "analytics": "Help us understand how visitors interact with our website",
                        "marketing": "Used to track visitors across websites for advertising purposes",
                        "preferences": "Remember your settings and preferences"
                    }
                },
                "4_managing_cookies": {
                    "title": "Managing Cookies",
                    "content": "You can control and/or delete cookies as you wish through your browser settings."
                }
            }
        }
    
    def _generate_dpa_template(self, company_name: str, contact_email: str) -> Dict[str, Any]:
        return {
            "title": f"Data Processing Agreement - {company_name}",
            "sections": {
                "1_definitions": {
                    "title": "Definitions",
                    "content": "This agreement defines the roles and responsibilities regarding personal data processing."
                },
                "2_processing_details": {
                    "title": "Details of Processing",
                    "content": "Categories of data subjects, types of personal data, and purposes of processing."
                },
                "3_obligations": {
                    "title": "Processor Obligations",
                    "content": "Security measures, data breach notification, and assistance with data subject requests."
                }
            }
        }
    
    async def _arun(self, document_type: str, company_info: Dict[str, Any], jurisdiction: str = "US") -> Dict[str, Any]:
        return self._run(document_type, company_info, jurisdiction)


class RegulatoryValidatorTool(BaseTool):
    """Tool for validating regulatory requirements"""
    name: str = "regulatory_validator"
    description: str = "Validate compliance with specific regulatory requirements"
    
    def _run(self, regulation: str, business_model: str, data_practices: Dict[str, Any]) -> Dict[str, Any]:
        validation_results = {
            "regulation": regulation,
            "business_model": business_model,
            "compliance_score": 0,
            "requirements_met": [],
            "requirements_missing": [],
            "recommendations": []
        }
        
        if regulation.upper() == "GDPR":
            gdpr_requirements = [
                "lawful_basis_defined",
                "privacy_policy_present",
                "cookie_consent_mechanism",
                "data_subject_rights_implemented",
                "data_breach_procedures",
                "privacy_by_design"
            ]
            
            # Simulate validation logic
            met_requirements = ["privacy_policy_present", "cookie_consent_mechanism"]
            missing_requirements = [req for req in gdpr_requirements if req not in met_requirements]
            
            validation_results.update({
                "compliance_score": len(met_requirements) / len(gdpr_requirements) * 100,
                "requirements_met": met_requirements,
                "requirements_missing": missing_requirements,
                "recommendations": [
                    "Define clear lawful basis for data processing",
                    "Implement data subject rights request handling",
                    "Establish data breach notification procedures",
                    "Conduct privacy impact assessments"
                ]
            })
        
        return validation_results
    
    async def _arun(self, regulation: str, business_model: str, data_practices: Dict[str, Any]) -> Dict[str, Any]:
        return self._run(regulation, business_model, data_practices)


class LegalAgent(LangGraphAgent):
    """Legal Agent responsible for compliance and legal document generation"""
    
    def __init__(self, memory_manager, approval_manager):
        personality = {
            "tone": "precise and thorough",
            "focus": "risk mitigation and compliance",
            "expertise": ["privacy law", "terms of service", "regulatory compliance", "data protection"],
            "model": "deepseek/deepseek-chat:free",
            "temperature": 0.3,
            "confidence_threshold": 0.8,
            "description": "Ensures legal compliance and generates legal documents"
        }
        
        super().__init__(
            name="Legal",
            role="Legal compliance and documentation specialist",
            memory_manager=memory_manager,
            approval_manager=approval_manager,
            personality=personality
        )
        
        # Initialize legal-specific tools
        self.tools = [
            ComplianceCheckerTool(),
            DocumentGeneratorTool(),
            RegulatoryValidatorTool()
        ]
        self.web_search = WebSearchTool()
    
    async def _execute_actions(self, state) -> Dict[str, Any]:
        """Execute legal-specific actions"""
        task = state["task"]
        context = state["context"]
        task_type = task.get("type", "general")
        
        if task_type == "compliance_check":
            return await self._perform_compliance_check(task, context)
        elif task_type == "generate_documents":
            return await self._generate_legal_documents(task, context)
        elif task_type == "regulatory_validation":
            return await self._validate_regulatory_compliance(task, context)
        else:
            return await self._general_legal_analysis(task, context)
    
    async def _perform_compliance_check(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive compliance check"""
        
        vision = context.get("vision", {})
        business_type = task.get("business_type", "technology")
        jurisdictions = task.get("jurisdictions", ["US", "EU"])
        data_handling = task.get("data_handling", "basic")
        
        # Use compliance checker tool
        compliance_tool = next(tool for tool in self.tools if tool.name == "compliance_checker")
        compliance_results = await compliance_tool._arun(
            business_type=business_type,
            jurisdictions=jurisdictions,
            data_handling=data_handling
        )
        
        # Add specific recommendations based on context
        recommendations = compliance_results.get("priority_actions", [])
        
        # Add business-specific recommendations
        if "data" in vision.get("description", "").lower():
            recommendations.extend([
                "Implement data minimization principles",
                "Establish data retention schedules",
                "Create data processing records"
            ])
        
        if "international" in vision.get("target_users", "").lower():
            recommendations.extend([
                "Review international data transfer mechanisms",
                "Consider Standard Contractual Clauses",
                "Evaluate adequacy decisions"
            ])
        
        compliance_analysis = {
            **compliance_results,
            "business_context": {
                "vision": vision.get("description", ""),
                "target_market": vision.get("target_users", ""),
                "data_processing": data_handling
            },
            "enhanced_recommendations": recommendations,
            "next_steps": [
                "Prioritize high-risk compliance areas",
                "Implement privacy by design principles",
                "Establish legal review processes",
                "Create compliance monitoring system"
            ],
            "estimated_timeline": {
                "immediate": "Privacy policy and ToS creation",
                "short_term": "Cookie consent implementation",
                "medium_term": "Data subject rights procedures",
                "long_term": "Ongoing compliance monitoring"
            }
        }
        
        await self.memory_manager.store_agent_memory(
            agent_name=self.name,
            memory_type="compliance_analysis",
            content=compliance_analysis,
            metadata={"task_id": task.get("id"), "created_at": datetime.now().isoformat()}
        )
        
        return compliance_analysis
    
    async def _generate_legal_documents(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate legal documents like ToS and Privacy Policy"""
        
        vision = context.get("vision", {})
        company_info = {
            "name": vision.get("name", "Your Company"),
            "email": task.get("contact_email", "legal@company.com"),
            "website": task.get("website", "www.company.com"),
            "description": vision.get("description", "")
        }
        
        document_types = task.get("document_types", ["terms_of_service", "privacy_policy"])
        jurisdiction = task.get("jurisdiction", "US")
        
        doc_generator = next(tool for tool in self.tools if tool.name == "document_generator")
        
        generated_documents = {}
        for doc_type in document_types:
            doc_result = await doc_generator._arun(
                document_type=doc_type,
                company_info=company_info,
                jurisdiction=jurisdiction
            )
            generated_documents[doc_type] = doc_result
        
        # Add implementation guidance
        implementation_guide = {
            "deployment_checklist": [
                "Review all placeholder text and customize",
                "Have documents reviewed by qualified attorney",
                "Implement cookie consent mechanism",
                "Set up data subject request handling",
                "Create document version control system",
                "Schedule regular policy reviews"
            ],
            "integration_requirements": {
                "website": "Add links to legal pages in footer",
                "signup_process": "Include checkbox for ToS acceptance",
                "cookie_banner": "Implement consent management platform",
                "data_collection": "Ensure privacy policy covers all data practices"
            },
            "maintenance_schedule": {
                "quarterly": "Review for business changes",
                "annually": "Full legal review and updates",
                "as_needed": "Update for new regulations or business model changes"
            }
        }
        
        legal_documents = {
            "documents": generated_documents,
            "implementation_guide": implementation_guide,
            "jurisdiction": jurisdiction,
            "company_info": company_info,
            "disclaimer": "These templates require customization and legal review before use",
            "generated_at": datetime.now().isoformat()
        }
        
        await self.memory_manager.store_agent_memory(
            agent_name=self.name,
            memory_type="legal_documents",
            content=legal_documents,
            metadata={"task_id": task.get("id"), "created_at": datetime.now().isoformat()}
        )
        
        return legal_documents
    
    async def _validate_regulatory_compliance(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate compliance with specific regulations"""
        
        regulation = task.get("regulation", "GDPR")
        business_model = context.get("vision", {}).get("description", "")
        data_practices = task.get("data_practices", {})
        
        validator_tool = next(tool for tool in self.tools if tool.name == "regulatory_validator")
        validation_results = await validator_tool._arun(
            regulation=regulation,
            business_model=business_model,
            data_practices=data_practices
        )
        
        # Add detailed action plan
        action_plan = {
            "immediate_actions": [],
            "short_term_goals": [],
            "long_term_objectives": []
        }
        
        for missing_req in validation_results.get("requirements_missing", []):
            if missing_req in ["privacy_policy_present", "cookie_consent_mechanism"]:
                action_plan["immediate_actions"].append(f"Implement {missing_req.replace('_', ' ')}")
            elif missing_req in ["data_subject_rights_implemented", "data_breach_procedures"]:
                action_plan["short_term_goals"].append(f"Establish {missing_req.replace('_', ' ')}")
            else:
                action_plan["long_term_objectives"].append(f"Develop {missing_req.replace('_', ' ')}")
        
        compliance_validation = {
            **validation_results,
            "action_plan": action_plan,
            "risk_assessment": {
                "high_risk": validation_results["compliance_score"] < 50,
                "medium_risk": 50 <= validation_results["compliance_score"] < 80,
                "low_risk": validation_results["compliance_score"] >= 80
            },
            "estimated_effort": {
                "hours_required": len(validation_results.get("requirements_missing", [])) * 8,
                "resources_needed": ["Legal counsel", "Development team", "Compliance officer"],
                "timeline_weeks": max(4, len(validation_results.get("requirements_missing", [])))
            }
        }
        
        await self.memory_manager.store_agent_memory(
            agent_name=self.name,
            memory_type="regulatory_validation",
            content=compliance_validation,
            metadata={"task_id": task.get("id"), "created_at": datetime.now().isoformat()}
        )
        
        return compliance_validation
    
    async def _general_legal_analysis(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """General legal analysis and risk assessment"""
        
        vision = context.get("vision", {})
        business_model = vision.get("description", "")
        target_users = vision.get("target_users", "")
        
        # Identify potential legal risks
        legal_risks = []
        
        if "data" in business_model.lower():
            legal_risks.append({
                "category": "Data Privacy",
                "risk": "Personal data processing without proper consent",
                "severity": "High",
                "mitigation": "Implement comprehensive privacy policy and consent mechanisms"
            })
        
        if "payment" in business_model.lower() or "financial" in business_model.lower():
            legal_risks.append({
                "category": "Financial Regulation",
                "risk": "Non-compliance with financial services regulations",
                "severity": "High",
                "mitigation": "Consult with financial services attorney and implement required compliance measures"
            })
        
        if "international" in target_users.lower():
            legal_risks.append({
                "category": "International Compliance",
                "risk": "Varying legal requirements across jurisdictions",
                "severity": "Medium",
                "mitigation": "Research and implement jurisdiction-specific compliance measures"
            })
        
        # General recommendations
        general_recommendations = [
            "Establish clear terms of service and privacy policy",
            "Implement proper data protection measures",
            "Set up legal entity structure appropriate for business model",
            "Consider intellectual property protection",
            "Establish customer support and dispute resolution processes",
            "Implement accessibility compliance measures",
            "Create content moderation policies if applicable"
        ]
        
        legal_analysis = {
            "business_overview": {
                "model": business_model,
                "target_users": target_users,
                "risk_profile": "Medium" if legal_risks else "Low"
            },
            "identified_risks": legal_risks,
            "general_recommendations": general_recommendations,
            "priority_areas": [
                "Privacy and data protection",
                "Terms of service",
                "Intellectual property",
                "Regulatory compliance"
            ],
            "legal_structure_recommendations": {
                "entity_type": "LLC or Corporation",
                "jurisdiction": "Delaware (US) for corporations",
                "considerations": ["Tax implications", "Liability protection", "Investment readiness"]
            },
            "ongoing_legal_needs": [
                "Regular policy updates",
                "Contract reviews",
                "Compliance monitoring",
                "Intellectual property management"
            ]
        }
        
        await self.memory_manager.store_agent_memory(
            agent_name=self.name,
            memory_type="legal_analysis",
            content=legal_analysis,
            metadata={"task_id": task.get("id"), "created_at": datetime.now().isoformat()}
        )
        
        # Get current legal trends
        legal_trends = await self._get_legal_trends(task, context)
        legal_analysis["current_trends"] = legal_trends
        
        return legal_analysis
    
    async def _get_legal_trends(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Get current legal and compliance trends"""
        try:
            vision_data = context.get("cofounder_output", {})
            vision_statement = vision_data.get("vision_statement", "")
            search_query = f"legal compliance trends {vision_statement[:50]} 2024"
            
            legal_data = await self.web_search._arun(search_query)
            
            return {
                "current_legal_trends": legal_data.get("summary", "Analysis in progress"),
                "regulatory_sources": len(legal_data.get("results", [])),
                "key_developments": [result.get("title", "") for result in legal_data.get("results", [])[:3]],
                "last_updated": legal_data.get("timestamp", "")
            }
        except Exception as e:
            return {"error": str(e), "fallback": "Manual legal research required"}