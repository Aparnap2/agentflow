"""
Enhanced Output Manager - Handles categorized outputs and PDF generation
"""

import os
import json
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
from loguru import logger
import weasyprint

from services.template_manager import template_manager

class EnhancedOutputManager:
    """Enhanced output manager with categorization and PDF generation"""
    
    def __init__(self):
        self.output_dir = Path("data/outputs")
        self.output_dir.mkdir(exist_ok=True, parents=True)
        
        # Create subdirectories
        (self.output_dir / "pdfs").mkdir(exist_ok=True)
        (self.output_dir / "docs").mkdir(exist_ok=True)
        (self.output_dir / "html").mkdir(exist_ok=True)
        (self.output_dir / "json").mkdir(exist_ok=True)
        
        # Output categories
        self.output_categories = {
            "content": ["blog_post", "social_media", "email_sequence"],
            "client": ["client_proposal", "client_onboarding", "client_followup"],
            "finance": ["financial_report", "invoice", "expense_report"],
            "research": ["market_research", "competitor_analysis", "trend_analysis"]
        }
        
        # Template mappings
        self.template_mappings = {
            "blog_post": "content/blog_post.j2",
            "social_media": "content/social_media.j2",
            "email_sequence": "content/email_sequence.j2",
            "client_proposal": "client/proposal.j2",
            "client_onboarding": "client/onboarding.j2",
            "client_followup": "client/followup.j2",
            "financial_report": "finance/financial_report.j2",
            "invoice": "finance/invoice.j2",
            "expense_report": "finance/expense_report.j2",
            "market_research": "research/market_research.j2",
            "competitor_analysis": "research/competitor_analysis.j2",
            "trend_analysis": "research/trend_analysis.j2"
        }
    
    def _determine_category(self, output_type: str) -> str:
        """Determine category based on output type"""
        for category, types in self.output_categories.items():
            if output_type in types:
                return category
        return "general"
    
    async def save_output(self, output_type: str, content: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Save output to file system"""
        # Generate ID
        output_id = f"{output_type}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Determine category
        category = self._determine_category(output_type)
        
        # Determine file extension
        if output_type in ["blog_post", "market_research", "competitor_analysis", "trend_analysis"]:
            ext = "md"
            subdir = "docs"
        elif output_type in ["email_sequence", "client_proposal", "client_onboarding", "client_followup"]:
            ext = "html"
            subdir = "html"
        elif output_type in ["financial_report", "invoice", "expense_report"]:
            ext = "json"
            subdir = "json"
        else:
            ext = "txt"
            subdir = "docs"
            
        # Create filename
        filename = f"{output_id}.{ext}"
        filepath = self.output_dir / subdir / filename
        
        # Save content
        with open(filepath, "w") as f:
            if isinstance(content, dict) or isinstance(content, list):
                json.dump(content, f, indent=2)
            else:
                f.write(str(content))
            
        # Save metadata
        meta_filepath = self.output_dir / subdir / f"{output_id}.meta.json"
        with open(meta_filepath, "w") as f:
            json.dump({
                "id": output_id,
                "type": output_type,
                "category": category,
                "created_at": datetime.now().isoformat(),
                "metadata": metadata or {}
            }, f, indent=2)
            
        logger.info(f"Saved output {output_id} to {filepath}")
            
        return {
            "id": output_id,
            "type": output_type,
            "category": category,
            "filename": filename,
            "path": str(filepath),
            "format": ext
        }
    
    async def generate_pdf(self, output_id: str, template_name: Optional[str] = None) -> Dict[str, Any]:
        """Generate PDF from output"""
        # Find output metadata
        meta_files = list(self.output_dir.glob(f"**/{output_id}.meta.json"))
        if not meta_files:
            raise ValueError(f"Output not found: {output_id}")
            
        meta_filepath = meta_files[0]
        
        # Load metadata
        with open(meta_filepath, "r") as f:
            metadata = json.load(f)
            
        # Determine output filepath
        output_type = metadata["type"]
        subdir = meta_filepath.parent.name
        output_filepath = meta_filepath.parent / f"{output_id}.{subdir}"
        
        # Load content
        if output_filepath.exists():
            with open(output_filepath, "r") as f:
                if output_filepath.suffix in [".json"]:
                    content = json.load(f)
                else:
                    content = f.read()
        else:
            raise ValueError(f"Output content not found: {output_filepath}")
        
        # Determine template
        if not template_name:
            template_name = self.template_mappings.get(output_type)
            if not template_name:
                raise ValueError(f"No template mapping for output type: {output_type}")
        
        # Prepare data for template
        template_data = {
            "content": content,
            "metadata": metadata,
            "generated_at": datetime.now().isoformat()
        }
        
        # If content is a dict, merge it with template_data
        if isinstance(content, dict):
            template_data.update(content)
        
        # Render template
        try:
            rendered = template_manager.render_file_template(template_name, template_data)
        except Exception as e:
            logger.error(f"Failed to render template: {e}")
            # Fallback to basic HTML
            rendered = f"""
            <html>
            <head>
                <title>{output_type.replace('_', ' ').title()}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 40px; }}
                    h1 {{ color: #333; }}
                    pre {{ background-color: #f5f5f5; padding: 10px; border-radius: 5px; }}
                </style>
            </head>
            <body>
                <h1>{output_type.replace('_', ' ').title()}</h1>
                <pre>{content}</pre>
                <p>Generated at: {datetime.now().isoformat()}</p>
            </body>
            </html>
            """
        
        # Generate PDF
        pdf_path = self.output_dir / "pdfs" / f"{output_id}.pdf"
        
        try:
            # Convert HTML to PDF
            weasyprint.HTML(string=rendered).write_pdf(pdf_path)
            
            logger.info(f"Generated PDF: {pdf_path}")
            
            return {
                "id": output_id,
                "pdf_path": str(pdf_path),
                "type": output_type,
                "category": metadata["category"]
            }
        except Exception as e:
            logger.error(f"Failed to generate PDF: {e}")
            raise
    
    async def get_output(self, output_id: str) -> Dict[str, Any]:
        """Get output by ID"""
        # Find output metadata
        meta_files = list(self.output_dir.glob(f"**/{output_id}.meta.json"))
        if not meta_files:
            raise ValueError(f"Output not found: {output_id}")
            
        meta_filepath = meta_files[0]
        
        # Load metadata
        with open(meta_filepath, "r") as f:
            metadata = json.load(f)
            
        # Determine output filepath
        subdir = meta_filepath.parent.name
        output_filepath = meta_filepath.parent / f"{output_id}.{subdir}"
        
        # Load content
        if output_filepath.exists():
            with open(output_filepath, "r") as f:
                if output_filepath.suffix in [".json"]:
                    content = json.load(f)
                else:
                    content = f.read()
        else:
            content = None
        
        return {
            "id": output_id,
            "type": metadata["type"],
            "category": metadata["category"],
            "content": content,
            "metadata": metadata,
            "path": str(output_filepath) if output_filepath.exists() else None
        }
    
    async def list_outputs(self, category: Optional[str] = None, output_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all outputs, optionally filtered by category or type"""
        outputs = []
        
        # Find all metadata files
        meta_files = list(self.output_dir.glob("**/*.meta.json"))
        
        for meta_filepath in meta_files:
            try:
                # Load metadata
                with open(meta_filepath, "r") as f:
                    metadata = json.load(f)
                
                # Apply filters
                if category and metadata.get("category") != category:
                    continue
                    
                if output_type and metadata.get("type") != output_type:
                    continue
                
                # Add to results
                outputs.append({
                    "id": metadata["id"],
                    "type": metadata["type"],
                    "category": metadata["category"],
                    "created_at": metadata["created_at"],
                    "has_pdf": (self.output_dir / "pdfs" / f"{metadata['id']}.pdf").exists()
                })
            except Exception as e:
                logger.error(f"Failed to process metadata file {meta_filepath}: {e}")
        
        # Sort by creation date (newest first)
        outputs.sort(key=lambda x: x["created_at"], reverse=True)
        
        return outputs
    
    async def delete_output(self, output_id: str) -> bool:
        """Delete an output"""
        # Find output metadata
        meta_files = list(self.output_dir.glob(f"**/{output_id}.meta.json"))
        if not meta_files:
            return False
            
        meta_filepath = meta_files[0]
        
        # Load metadata
        with open(meta_filepath, "r") as f:
            metadata = json.load(f)
            
        # Delete metadata file
        meta_filepath.unlink()
        
        # Delete content file
        subdir = meta_filepath.parent.name
        output_filepath = meta_filepath.parent / f"{output_id}.{subdir}"
        if output_filepath.exists():
            output_filepath.unlink()
        
        # Delete PDF if exists
        pdf_path = self.output_dir / "pdfs" / f"{output_id}.pdf"
        if pdf_path.exists():
            pdf_path.unlink()
        
        logger.info(f"Deleted output: {output_id}")
        return True
    
    async def search_outputs(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search outputs by content or metadata"""
        results = []
        
        # Find all metadata files
        meta_files = list(self.output_dir.glob("**/*.meta.json"))
        
        for meta_filepath in meta_files:
            try:
                # Load metadata
                with open(meta_filepath, "r") as f:
                    metadata = json.load(f)
                
                # Check if query matches metadata
                metadata_str = json.dumps(metadata).lower()
                if query.lower() in metadata_str:
                    results.append({
                        "id": metadata["id"],
                        "type": metadata["type"],
                        "category": metadata["category"],
                        "created_at": metadata["created_at"],
                        "match_type": "metadata",
                        "has_pdf": (self.output_dir / "pdfs" / f"{metadata['id']}.pdf").exists()
                    })
                    continue
                
                # Check content file
                subdir = meta_filepath.parent.name
                output_filepath = meta_filepath.parent / f"{metadata['id']}.{subdir}"
                if output_filepath.exists():
                    with open(output_filepath, "r") as f:
                        content = f.read().lower()
                        if query.lower() in content:
                            results.append({
                                "id": metadata["id"],
                                "type": metadata["type"],
                                "category": metadata["category"],
                                "created_at": metadata["created_at"],
                                "match_type": "content",
                                "has_pdf": (self.output_dir / "pdfs" / f"{metadata['id']}.pdf").exists()
                            })
            except Exception as e:
                logger.error(f"Failed to process metadata file {meta_filepath}: {e}")
                
            # Limit results
            if len(results) >= limit:
                break
        
        # Sort by creation date (newest first)
        results.sort(key=lambda x: x["created_at"], reverse=True)
        
        return results
    
    async def get_output_categories(self) -> Dict[str, List[str]]:
        """Get all output categories and types"""
        return self.output_categories
    
    async def get_template_mappings(self) -> Dict[str, str]:
        """Get template mappings for output types"""
        return self.template_mappings
    
    async def update_template_mapping(self, output_type: str, template_name: str) -> bool:
        """Update template mapping for an output type"""
        if output_type not in [item for sublist in self.output_categories.values() for item in sublist]:
            return False
            
        self.template_mappings[output_type] = template_name
        return True

# Global instance
output_manager = EnhancedOutputManager()