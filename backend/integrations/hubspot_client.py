"""
HubSpot CRM Integration Client
Implements CRM-centric operations per PRD requirements
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
from pydantic import BaseModel
from .base_integration import BaseIntegration, IntegrationConfig
from loguru import logger

class HubSpotContact(BaseModel):
    """HubSpot contact data model"""
    email: str
    firstname: Optional[str] = None
    lastname: Optional[str] = None
    company: Optional[str] = None
    phone: Optional[str] = None
    lifecyclestage: Optional[str] = None
    lead_status: Optional[str] = None

class HubSpotDeal(BaseModel):
    """HubSpot deal data model"""
    dealname: str
    amount: Optional[float] = None
    dealstage: str
    pipeline: Optional[str] = None
    closedate: Optional[datetime] = None
    hubspot_owner_id: Optional[str] = None

class HubSpotClient(BaseIntegration):
    """HubSpot CRM API client for CRM-centric operations"""
    
    def __init__(self, config: IntegrationConfig):
        super().__init__(config)
        self.base_url = "https://api.hubapi.com"
        
    async def authenticate(self) -> bool:
        """Authenticate with HubSpot API"""
        try:
            result = await self.make_request("GET", "/oauth/v1/access-tokens/validate")
            logger.info("HubSpot authentication successful")
            return True
        except Exception as e:
            logger.error(f"HubSpot authentication failed: {e}")
            return False
            
    async def health_check(self) -> Dict[str, Any]:
        """Check HubSpot API connectivity"""
        try:
            await self.make_request("GET", "/oauth/v1/access-tokens/validate")
            return {"status": "healthy", "service": "hubspot"}
        except Exception as e:
            return {"status": "unhealthy", "service": "hubspot", "error": str(e)}
    
    # Contact Management
    
    async def create_contact(self, contact: HubSpotContact) -> Dict[str, Any]:
        """Create new contact in HubSpot"""
        contact_data = {
            "properties": contact.dict(exclude_none=True)
        }
        
        result = await self.make_request("POST", "/crm/v3/objects/contacts", contact_data)
        logger.info(f"HubSpot contact created: {result.get('id')}")
        return result
    
    async def get_contact(self, contact_id: str) -> Dict[str, Any]:
        """Get contact by ID"""
        return await self.make_request("GET", f"/crm/v3/objects/contacts/{contact_id}")
    
    async def get_contact_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get contact by email address"""
        try:
            result = await self.make_request(
                "GET", 
                f"/crm/v3/objects/contacts/{email}?idProperty=email"
            )
            return result
        except Exception as e:
            if "404" in str(e):
                return None
            raise e
    
    async def update_contact(self, contact_id: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Update contact properties"""
        update_data = {"properties": properties}
        return await self.make_request("PATCH", f"/crm/v3/objects/contacts/{contact_id}", update_data)
    
    async def search_contacts(self, filters: List[Dict[str, Any]], limit: int = 100) -> Dict[str, Any]:
        """Search contacts with filters"""
        search_data = {
            "filterGroups": [{"filters": filters}],
            "limit": limit,
            "properties": ["email", "firstname", "lastname", "company", "lifecyclestage", "lead_status"]
        }
        
        return await self.make_request("POST", "/crm/v3/objects/contacts/search", search_data)
    
    # Deal Management
    
    async def create_deal(self, deal: HubSpotDeal, contact_id: Optional[str] = None) -> Dict[str, Any]:
        """Create new deal in HubSpot"""
        deal_data = {
            "properties": deal.dict(exclude_none=True)
        }
        
        # Convert datetime to timestamp
        if deal.closedate:
            deal_data["properties"]["closedate"] = int(deal.closedate.timestamp() * 1000)
        
        result = await self.make_request("POST", "/crm/v3/objects/deals", deal_data)
        
        # Associate with contact if provided
        if contact_id and result.get("id"):
            await self.associate_deal_with_contact(result["id"], contact_id)
        
        logger.info(f"HubSpot deal created: {result.get('id')}")
        return result
    
    async def get_deal(self, deal_id: str) -> Dict[str, Any]:
        """Get deal by ID"""
        return await self.make_request("GET", f"/crm/v3/objects/deals/{deal_id}")
    
    async def update_deal(self, deal_id: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Update deal properties"""
        update_data = {"properties": properties}
        return await self.make_request("PATCH", f"/crm/v3/objects/deals/{deal_id}", update_data)
    
    async def move_deal_stage(self, deal_id: str, new_stage: str, reason: str = "") -> Dict[str, Any]:
        """Move deal to new stage with audit trail"""
        properties = {
            "dealstage": new_stage,
            "notes_last_updated": datetime.now().isoformat()
        }
        
        if reason:
            properties["hs_deal_stage_probability"] = reason
        
        result = await self.update_deal(deal_id, properties)
        
        # Log stage change
        await self.add_deal_note(deal_id, f"Deal moved to {new_stage}. Reason: {reason}")
        
        return result
    
    async def get_deals_by_stage(self, stage: str, limit: int = 100) -> Dict[str, Any]:
        """Get deals by stage"""
        filters = [{"propertyName": "dealstage", "operator": "EQ", "value": stage}]
        search_data = {
            "filterGroups": [{"filters": filters}],
            "limit": limit,
            "properties": ["dealname", "amount", "dealstage", "closedate", "hubspot_owner_id"]
        }
        
        return await self.make_request("POST", "/crm/v3/objects/deals/search", search_data)
    
    # Pipeline Management
    
    async def get_pipelines(self) -> Dict[str, Any]:
        """Get all deal pipelines"""
        return await self.make_request("GET", "/crm/v3/pipelines/deals")
    
    async def get_pipeline_stages(self, pipeline_id: str) -> Dict[str, Any]:
        """Get stages for a specific pipeline"""
        pipelines = await self.get_pipelines()
        for pipeline in pipelines.get("results", []):
            if pipeline["id"] == pipeline_id:
                return {"stages": pipeline.get("stages", [])}
        return {"stages": []}
    
    # Associations
    
    async def associate_deal_with_contact(self, deal_id: str, contact_id: str) -> Dict[str, Any]:
        """Associate deal with contact"""
        association_data = {
            "inputs": [{
                "from": {"id": deal_id},
                "to": {"id": contact_id},
                "type": "deal_to_contact"
            }]
        }
        
        return await self.make_request("POST", "/crm/v3/associations/deals/contacts/batch/create", association_data)
    
    async def get_contact_deals(self, contact_id: str) -> Dict[str, Any]:
        """Get all deals associated with a contact"""
        return await self.make_request("GET", f"/crm/v3/objects/contacts/{contact_id}/associations/deals")
    
    # Notes and Activities
    
    async def add_contact_note(self, contact_id: str, note: str) -> Dict[str, Any]:
        """Add note to contact"""
        note_data = {
            "properties": {
                "hs_note_body": note,
                "hs_timestamp": datetime.now().isoformat()
            }
        }
        
        result = await self.make_request("POST", "/crm/v3/objects/notes", note_data)
        
        # Associate note with contact
        if result.get("id"):
            await self.make_request(
                "POST", 
                f"/crm/v3/objects/notes/{result['id']}/associations/contacts/{contact_id}/note_to_contact"
            )
        
        return result
    
    async def add_deal_note(self, deal_id: str, note: str) -> Dict[str, Any]:
        """Add note to deal"""
        note_data = {
            "properties": {
                "hs_note_body": note,
                "hs_timestamp": datetime.now().isoformat()
            }
        }
        
        result = await self.make_request("POST", "/crm/v3/objects/notes", note_data)
        
        # Associate note with deal
        if result.get("id"):
            await self.make_request(
                "POST", 
                f"/crm/v3/objects/notes/{result['id']}/associations/deals/{deal_id}/note_to_deal"
            )
        
        return result
    
    # Lead Health Scoring
    
    async def calculate_lead_health_score(self, contact_id: str) -> Dict[str, Any]:
        """Calculate lead health score based on HubSpot data"""
        try:
            # Get contact details
            contact = await self.get_contact(contact_id)
            properties = contact.get("properties", {})
            
            # Get associated deals
            deals = await self.get_contact_deals(contact_id)
            
            # Calculate health score
            score = 0
            factors = []
            
            # Contact completeness (0-30 points)
            if properties.get("email"):
                score += 10
                factors.append("Has email")
            if properties.get("phone"):
                score += 5
                factors.append("Has phone")
            if properties.get("company"):
                score += 10
                factors.append("Has company")
            if properties.get("firstname") and properties.get("lastname"):
                score += 5
                factors.append("Complete name")
            
            # Lifecycle stage (0-25 points)
            lifecycle = properties.get("lifecyclestage", "")
            if lifecycle == "customer":
                score += 25
                factors.append("Existing customer")
            elif lifecycle == "opportunity":
                score += 20
                factors.append("Qualified opportunity")
            elif lifecycle == "lead":
                score += 15
                factors.append("Qualified lead")
            elif lifecycle == "subscriber":
                score += 10
                factors.append("Engaged subscriber")
            
            # Deal activity (0-25 points)
            deal_count = len(deals.get("results", []))
            if deal_count > 0:
                score += min(25, deal_count * 5)
                factors.append(f"{deal_count} associated deals")
            
            # Recent activity (0-20 points)
            last_activity = properties.get("notes_last_updated")
            if last_activity:
                # Would calculate based on recency
                score += 15
                factors.append("Recent activity")
            
            # Normalize to 0-100
            health_score = min(100, score)
            
            # Determine health level
            if health_score >= 80:
                health_level = "excellent"
            elif health_score >= 60:
                health_level = "good"
            elif health_score >= 40:
                health_level = "fair"
            else:
                health_level = "poor"
            
            return {
                "contact_id": contact_id,
                "health_score": health_score,
                "health_level": health_level,
                "contributing_factors": factors,
                "recommendations": self._get_health_recommendations(health_score, properties),
                "calculated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate health score: {e}")
            return {"error": str(e)}
    
    def _get_health_recommendations(self, score: int, properties: Dict[str, Any]) -> List[str]:
        """Get recommendations based on health score"""
        recommendations = []
        
        if score < 40:
            recommendations.append("Complete contact information")
            recommendations.append("Schedule discovery call")
            recommendations.append("Send educational content")
        elif score < 60:
            recommendations.append("Nurture with targeted content")
            recommendations.append("Schedule follow-up meeting")
        elif score < 80:
            recommendations.append("Present solution proposal")
            recommendations.append("Identify decision makers")
        else:
            recommendations.append("Focus on retention and expansion")
            recommendations.append("Request referrals")
        
        # Specific recommendations based on missing data
        if not properties.get("phone"):
            recommendations.append("Collect phone number")
        if not properties.get("company"):
            recommendations.append("Identify company/organization")
        
        return recommendations
    
    # Analytics and Reporting
    
    async def get_pipeline_analytics(self, pipeline_id: Optional[str] = None) -> Dict[str, Any]:
        """Get pipeline analytics"""
        try:
            # Get all deals or deals in specific pipeline
            if pipeline_id:
                filters = [{"propertyName": "pipeline", "operator": "EQ", "value": pipeline_id}]
                search_data = {
                    "filterGroups": [{"filters": filters}],
                    "limit": 1000,
                    "properties": ["dealname", "amount", "dealstage", "closedate", "pipeline"]
                }
                deals_result = await self.make_request("POST", "/crm/v3/objects/deals/search", search_data)
            else:
                deals_result = await self.make_request("GET", "/crm/v3/objects/deals?limit=1000")
            
            deals = deals_result.get("results", [])
            
            # Calculate analytics
            total_deals = len(deals)
            total_value = sum(float(deal.get("properties", {}).get("amount", 0) or 0) for deal in deals)
            
            # Group by stage
            stage_breakdown = {}
            for deal in deals:
                stage = deal.get("properties", {}).get("dealstage", "unknown")
                if stage not in stage_breakdown:
                    stage_breakdown[stage] = {"count": 0, "value": 0}
                stage_breakdown[stage]["count"] += 1
                stage_breakdown[stage]["value"] += float(deal.get("properties", {}).get("amount", 0) or 0)
            
            return {
                "pipeline_id": pipeline_id,
                "total_deals": total_deals,
                "total_value": total_value,
                "average_deal_size": total_value / total_deals if total_deals > 0 else 0,
                "stage_breakdown": stage_breakdown,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get pipeline analytics: {e}")
            return {"error": str(e)}
    
    async def make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make authenticated request to HubSpot API"""
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                if method == "GET":
                    response = await client.get(url, headers=headers)
                elif method == "POST":
                    response = await client.post(url, headers=headers, json=data)
                elif method == "PATCH":
                    response = await client.patch(url, headers=headers, json=data)
                elif method == "DELETE":
                    response = await client.delete(url, headers=headers)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                response.raise_for_status()
                return response.json() if response.content else {}
                
        except Exception as e:
            logger.error(f"HubSpot API request failed: {method} {endpoint} - {e}")
            raise e