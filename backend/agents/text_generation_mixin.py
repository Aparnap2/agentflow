"""
Text Generation Mixin - Adds text generation capabilities to agents
"""
from typing import Dict, Any, List, Optional, Literal
from loguru import logger
from services.template_manager import template_manager
from services.document_converter import document_converter

class TextGenerationMixin:
    """Mixin class to add text generation capabilities to agents"""
    
    async def generate_text(self, template_name: str, data: Dict[str, Any]) -> str:
        """Generate text using a template"""
        try:
            # Render template with data
            return template_manager.render_template(template_name, data)
        except Exception as e:
            logger.error(f"Failed to generate text: {e}")
            raise ValueError(f"Failed to generate text: {e}")
    
    async def generate_document(self, template_name: str, data: Dict[str, Any], 
                              doc_type: str, filename: str,
                              format: Literal["pdf", "docx", "md", "html", "txt"] = "pdf",
                              metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate a document using a template and convert to specified format"""
        try:
            # Generate text content
            content = await self.generate_text(template_name, data)
            
            # Add agent-specific enhancements
            enhanced_content = await self._enhance_content(content, doc_type, format)
            
            # Prepare metadata
            doc_metadata = {
                "generated_by": self.name if hasattr(self, "name") else "Unknown Agent",
                "template": template_name,
                **metadata or {}
            }
            
            # Generate document
            doc_info = document_converter.generate_document(
                enhanced_content, doc_type, filename, format, doc_metadata
            )
            
            logger.info(f"Generated {format} document: {filename}")
            return doc_info
            
        except Exception as e:
            logger.error(f"Failed to generate document: {e}")
            raise ValueError(f"Failed to generate document: {e}")
    
    async def _enhance_content(self, content: str, doc_type: str, 
                             format: str) -> str:
        """Enhance content based on agent specialization (to be overridden by specific agents)"""
        # Default implementation - no enhancement
        return content
    
    async def list_available_templates(self) -> List[Dict[str, Any]]:
        """List available templates for this agent"""
        agent_type = self._get_agent_type()
        return template_manager.list_templates(agent_type)
    
    def _get_agent_type(self) -> str:
        """Get agent type based on class name"""
        if hasattr(self, "name"):
            agent_name = self.name.lower()
            
            # Map agent names to template types
            type_mapping = {
                "marketing": "marketing",
                "finance": "finance",
                "sales": "sales",
                "legal": "legal",
                "operations": "operations",
                "research": "research",
                "cofounder": "marketing",  # Default mappings for other agents
                "manager": "operations",
                "product": "operations",
                "customer": "sales",
                "hr": "operations",
                "tech": "operations"
            }
            
            # Return mapped type or default to "operations"
            return type_mapping.get(agent_name, "operations")
        
        return "operations"  # Default type
    
    async def create_template(self, template_name: str, content: str) -> str:
        """Create a new template for this agent"""
        agent_type = self._get_agent_type()
        return template_manager.create_template(agent_type, template_name, content)
    
    async def get_template_content(self, template_path: str) -> Optional[str]:
        """Get the raw content of a template"""
        return template_manager.get_template_content(template_path)
    
    async def update_template(self, template_path: str, content: str) -> bool:
        """Update an existing template"""
        return template_manager.update_template(template_path, content)
    
    async def delete_template(self, template_path: str) -> bool:
        """Delete a template"""
        return template_manager.delete_template(template_path)