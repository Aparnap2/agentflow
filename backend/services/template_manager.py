"""
Template Manager Service - Handles template storage, rendering, and management
"""
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from jinja2 import Environment, BaseLoader, Template, FileSystemLoader, select_autoescape
from loguru import logger

from database.neo4j_client import Neo4jClient
from utils.text_utils import sanitize_template_name

class TemplateManager:
    """Manages document templates with Neo4j storage and Jinja2 rendering"""
    
    def __init__(self):
        self.neo4j = Neo4jClient()
        self.jinja_env = Environment(
            loader=BaseLoader(),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Set up file-based templates as well
        self.templates_dir = Path("data/templates")
        self.templates_dir.mkdir(exist_ok=True, parents=True)
        
        self.env = Environment(
            loader=FileSystemLoader(self.templates_dir),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Register custom filters
        self.jinja_env.filters['currency'] = self._currency_filter
        self.jinja_env.filters['date'] = self._date_filter
        
        # Register same filters for file-based environment
        self.env.filters['currency'] = self._currency_filter
        self.env.filters['date'] = self._date_filter
    
    async def store_template(self, 
                           name: str, 
                           content: str, 
                           agent_type: str,
                           metadata: Optional[Dict[str, Any]] = None) -> str:
        """Store a template in Neo4j"""
        try:
            # Validate template syntax
            self.jinja_env.from_string(content)
            
            # Sanitize template name
            safe_name = sanitize_template_name(name)
            
            # Store in Neo4j
            query = """
            MERGE (t:Template {name: $name})
            SET t.content = $content,
                t.agent_type = $agent_type,
                t.metadata = $metadata,
                t.updated_at = datetime()
            RETURN t.name as name
            """
            
            result = await self.neo4j.execute_query(
                query,
                {
                    "name": safe_name,
                    "content": content,
                    "agent_type": agent_type,
                    "metadata": json.dumps(metadata or {})
                }
            )
            
            logger.info(f"Stored template: {safe_name}")
            return safe_name
            
        except Exception as e:
            logger.error(f"Failed to store template: {e}")
            raise
    
    async def get_template(self, name: str) -> Optional[Dict[str, Any]]:
        """Retrieve a template from Neo4j"""
        try:
            query = """
            MATCH (t:Template {name: $name})
            RETURN t.content as content,
                   t.agent_type as agent_type,
                   t.metadata as metadata,
                   t.updated_at as updated_at
            """
            
            result = await self.neo4j.execute_query(query, {"name": name})
            
            if not result:
                return None
                
            template_data = result[0]
            return {
                "name": name,
                "content": template_data["content"],
                "agent_type": template_data["agent_type"],
                "metadata": json.loads(template_data["metadata"]),
                "updated_at": template_data["updated_at"]
            }
            
        except Exception as e:
            logger.error(f"Failed to get template: {e}")
            raise
    
    async def list_templates(self, agent_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all templates, optionally filtered by agent type"""
        try:
            query = """
            MATCH (t:Template)
            WHERE $agent_type IS NULL OR t.agent_type = $agent_type
            RETURN t.name as name,
                   t.agent_type as agent_type,
                   t.metadata as metadata,
                   t.updated_at as updated_at
            """
            
            results = await self.neo4j.execute_query(query, {"agent_type": agent_type})
            
            return [{
                "name": result["name"],
                "agent_type": result["agent_type"],
                "metadata": json.loads(result["metadata"]),
                "updated_at": result["updated_at"]
            } for result in results]
            
        except Exception as e:
            logger.error(f"Failed to list templates: {e}")
            raise
    
    async def render_template(self, 
                            name: str, 
                            data: Dict[str, Any],
                            validate: bool = True) -> str:
        """Render a template with provided data"""
        try:
            # Get template
            template_data = await self.get_template(name)
            if not template_data:
                raise ValueError(f"Template not found: {name}")
            
            # Create template
            template = self.jinja_env.from_string(template_data["content"])
            
            # Validate data if requested
            if validate:
                self._validate_template_data(template, data)
            
            # Render template
            rendered = template.render(**data)
            
            return rendered
            
        except Exception as e:
            logger.error(f"Failed to render template: {e}")
            raise
    
    def _validate_template_data(self, template: Template, data: Dict[str, Any]):
        """Validate that all required template variables are provided"""
        required_vars = set()
        
        def visit_node(node):
            if hasattr(node, 'name'):
                if node.name == 'Name':
                    required_vars.add(node.node.name)
            for child in node.iter_child_nodes():
                visit_node(child)
        
        visit_node(template.environment.parse(template.source))
        
        missing_vars = required_vars - set(data.keys())
        if missing_vars:
            raise ValueError(f"Missing required template variables: {missing_vars}")
    
    def _currency_filter(self, value: float) -> str:
        """Format number as currency"""
        try:
            return "${:,.2f}".format(float(value))
        except (ValueError, TypeError):
            return str(value)
    
    def _date_filter(self, value: str, format: str = "%Y-%m-%d") -> str:
        """Format date string"""
        try:
            if isinstance(value, str):
                dt = datetime.fromisoformat(value)
            elif isinstance(value, datetime):
                dt = value
            else:
                return str(value)
            return dt.strftime(format)
        except (ValueError, TypeError):
            return str(value)
            
    async def create_default_templates(self):
        """Create default templates for each agent type"""
        # Market Research Template
        market_research_template = """# Market Research Report: {{ market_segment }}

## Executive Summary
{{ executive_summary }}

## Market Overview
{{ market_overview }}

## Target Audience Analysis
{% for audience in target_audiences %}
### {{ audience.name }}
- **Demographics:** {{ audience.demographics }}
- **Pain Points:** {{ audience.pain_points }}
- **Opportunities:** {{ audience.opportunities }}

{% endfor %}

## Competitive Analysis
{% for competitor in competitors %}
### {{ competitor.name }}
- **Strengths:** {{ competitor.strengths }}
- **Weaknesses:** {{ competitor.weaknesses }}
- **Market Share:** {{ competitor.market_share }}

{% endfor %}

## SWOT Analysis
### Strengths
{% for item in swot.strengths %}
- {{ item }}
{% endfor %}

### Weaknesses
{% for item in swot.weaknesses %}
- {{ item }}
{% endfor %}

### Opportunities
{% for item in swot.opportunities %}
- {{ item }}
{% endfor %}

### Threats
{% for item in swot.threats %}
- {{ item }}
{% endfor %}

## Recommendations
{% for recommendation in recommendations %}
- {{ recommendation }}
{% endfor %}

## Conclusion
{{ conclusion }}
"""
        
        # Blog Post Template
        blog_post_template = """# {{ title }}

{{ meta_description }}

## Introduction
{{ introduction }}

{% for section in content_sections %}
## {{ section.heading }}
{{ section.content }}

{% endfor %}

## Conclusion
{{ conclusion }}

{% if call_to_action %}
**{{ call_to_action }}**
{% endif %}
"""

        # Client Proposal Template
        client_proposal_template = """# {{ project_name }} Proposal

## Executive Summary
{{ executive_summary }}

## Client Background
{{ client_background }}

## Project Scope
{{ project_scope }}

## Proposed Solution
{% for solution_item in proposed_solution %}
### {{ solution_item.title }}
{{ solution_item.description }}

{% endfor %}

## Timeline
{% for phase in timeline %}
### Phase {{ loop.index }}: {{ phase.name }}
- **Duration:** {{ phase.duration }}
- **Deliverables:** {{ phase.deliverables }}
- **Key Activities:** {{ phase.activities }}

{% endfor %}

## Investment
{% for tier in pricing_tiers %}
### {{ tier.name }} - {{ tier.price | currency }}
{{ tier.description }}

**Includes:**
{% for item in tier.includes %}
- {{ item }}
{% endfor %}

{% endfor %}

## Next Steps
{% for step in next_steps %}
{{ loop.index }}. {{ step }}
{% endfor %}

## Terms & Conditions
{{ terms_and_conditions }}
"""

        # Invoice Template
        invoice_template = """# INVOICE

**Invoice #:** {{ invoice_number }}
**Date:** {{ invoice_date | date }}
**Due Date:** {{ due_date | date }}

## From
{{ company_name }}
{{ company_address }}
{{ company_email }}
{{ company_phone }}

## To
{{ client_name }}
{{ client_address }}
{{ client_email }}

## Items
| Description | Quantity | Rate | Amount |
|-------------|----------|------|--------|
{% for item in items %}
| {{ item.description }} | {{ item.quantity }} | {{ item.rate | currency }} | {{ item.amount | currency }} |
{% endfor %}

## Summary
**Subtotal:** {{ subtotal | currency }}
{% if tax_rate %}**Tax ({{ tax_rate }}%):** {{ tax_amount | currency }}{% endif %}
**Total:** {{ total | currency }}

## Payment Instructions
{{ payment_instructions }}

## Terms
{{ payment_terms }}
"""

        # Default templates dictionary
        default_templates = {
            "research/market_research.j2": market_research_template,
            "content/blog_post.j2": blog_post_template,
            "client/proposal.j2": client_proposal_template,
            "finance/invoice.j2": invoice_template
        }
        
        # Create each default template
        for template_path, template_content in default_templates.items():
            file_path = self.templates_dir / template_path
            file_path.parent.mkdir(exist_ok=True)
            with open(file_path, 'w') as f:
                f.write(template_content)
        
        logger.info(f"Created {len(default_templates)} default templates")
    
    def get_file_template(self, template_name: str) -> Template:
        """Get a template by name from file system"""
        try:
            return self.env.get_template(template_name)
        except Exception as e:
            logger.error(f"Failed to get template {template_name}: {e}")
            raise ValueError(f"Template not found: {template_name}")
    
    def render_file_template(self, template_name: str, data: Dict[str, Any]) -> str:
        """Render a template from file system with provided data"""
        try:
            template = self.get_file_template(template_name)
            return template.render(**data)
        except Exception as e:
            logger.error(f"Failed to render template {template_name}: {e}")
            raise ValueError(f"Failed to render template: {e}")
    
    def create_template(self, template_type: str, template_name: str, content: str) -> str:
        """Create a new template in file system"""
        # Sanitize template name
        safe_name = sanitize_template_name(template_name)
        if not safe_name.endswith('.j2'):
            safe_name += '.j2'
        
        # Create full path
        template_path = f"{template_type}/{safe_name}"
        file_path = self.templates_dir / template_path
        
        # Ensure directory exists
        file_path.parent.mkdir(exist_ok=True)
        
        # Write template
        with open(file_path, 'w') as f:
            f.write(content)
        
        logger.info(f"Created template: {template_path}")
        return template_path
    
    def list_file_templates(self, template_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List available templates from file system"""
        templates = []
        
        if template_type:
            # List templates of specific type
            template_dir = self.templates_dir / template_type
            if not template_dir.exists():
                return []
            
            for file_path in template_dir.glob("*.j2"):
                templates.append({
                    "name": file_path.stem,
                    "path": f"{template_type}/{file_path.name}",
                    "type": template_type,
                    "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                })
        else:
            # List all templates
            for template_dir in self.templates_dir.iterdir():
                if template_dir.is_dir():
                    type_name = template_dir.name
                    for file_path in template_dir.glob("*.j2"):
                        templates.append({
                            "name": file_path.stem,
                            "path": f"{type_name}/{file_path.name}",
                            "type": type_name,
                            "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                        })
        
        return templates
    
    def delete_template(self, template_path: str) -> bool:
        """Delete a template from file system"""
        try:
            file_path = self.templates_dir / template_path
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Deleted template: {template_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete template {template_path}: {e}")
            return False
    
    def update_template(self, template_path: str, content: str) -> bool:
        """Update an existing template in file system"""
        try:
            file_path = self.templates_dir / template_path
            if not file_path.exists():
                return False
            
            with open(file_path, 'w') as f:
                f.write(content)
            
            logger.info(f"Updated template: {template_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to update template {template_path}: {e}")
            return False
    
    def get_template_content(self, template_path: str) -> Optional[str]:
        """Get the raw content of a template from file system"""
        try:
            file_path = self.templates_dir / template_path
            if not file_path.exists():
                return None
            
            with open(file_path, 'r') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to read template {template_path}: {e}")
            return None

# Global instance
template_manager = TemplateManager()