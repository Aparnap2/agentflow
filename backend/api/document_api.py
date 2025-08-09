"""
Document API - Endpoints for document generation and management
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, File, UploadFile
from typing import Dict, Any, List, Optional, Literal
from pydantic import BaseModel
from datetime import datetime
from loguru import logger

from coordination.enhanced_orchestrator import get_enhanced_orchestrator
from services.template_manager import template_manager
from services.document_converter import document_converter

router = APIRouter(
    prefix="/documents",
    tags=["documents"],
    responses={404: {"description": "Not found"}},
)

# Models
class TemplateRequest(BaseModel):
    template_type: str
    template_name: str
    content: str

class TemplateUpdateRequest(BaseModel):
    content: str

class DocumentRequest(BaseModel):
    template_name: str
    agent_name: str
    data: Dict[str, Any]
    doc_type: str
    filename: str
    format: Literal["pdf", "docx", "md", "html", "txt"] = "pdf"
    metadata: Optional[Dict[str, Any]] = None

class ScheduledDocumentRequest(BaseModel):
    template_name: str
    agent_name: str
    data: Dict[str, Any]
    doc_type: str
    filename: str
    format: Literal["pdf", "docx", "md", "html", "txt"] = "pdf"
    metadata: Optional[Dict[str, Any]] = None
    schedule: str  # Cron expression
    description: str

# Template management endpoints
@router.get("/templates")
async def list_templates(template_type: Optional[str] = None):
    """List available templates"""
    try:
        templates = template_manager.list_templates(template_type)
        return {"templates": templates}
    except Exception as e:
        logger.error(f"Failed to list templates: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list templates: {str(e)}")

@router.post("/templates")
async def create_template(request: TemplateRequest):
    """Create a new template"""
    try:
        template_path = template_manager.create_template(
            request.template_type, request.template_name, request.content
        )
        return {"status": "success", "template_path": template_path}
    except Exception as e:
        logger.error(f"Failed to create template: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create template: {str(e)}")

@router.get("/templates/{template_type}/{template_name}")
async def get_template(template_type: str, template_name: str):
    """Get template content"""
    try:
        template_path = f"{template_type}/{template_name}"
        if not template_name.endswith('.j2'):
            template_path += '.j2'
            
        content = template_manager.get_template_content(template_path)
        if content is None:
            raise HTTPException(status_code=404, detail=f"Template not found: {template_path}")
        
        return {"content": content, "template_path": template_path}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get template: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get template: {str(e)}")

@router.put("/templates/{template_type}/{template_name}")
async def update_template(template_type: str, template_name: str, request: TemplateUpdateRequest):
    """Update an existing template"""
    try:
        template_path = f"{template_type}/{template_name}"
        if not template_name.endswith('.j2'):
            template_path += '.j2'
            
        success = template_manager.update_template(template_path, request.content)
        if not success:
            raise HTTPException(status_code=404, detail=f"Template not found: {template_path}")
        
        return {"status": "success", "template_path": template_path}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update template: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update template: {str(e)}")

@router.delete("/templates/{template_type}/{template_name}")
async def delete_template(template_type: str, template_name: str):
    """Delete a template"""
    try:
        template_path = f"{template_type}/{template_name}"
        if not template_name.endswith('.j2'):
            template_path += '.j2'
            
        success = template_manager.delete_template(template_path)
        if not success:
            raise HTTPException(status_code=404, detail=f"Template not found: {template_path}")
        
        return {"status": "success", "template_path": template_path}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete template: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete template: {str(e)}")

# Document generation endpoints
@router.post("/generate")
async def generate_document(request: DocumentRequest, background_tasks: BackgroundTasks):
    """Generate a document using a template"""
    try:
        orchestrator = get_enhanced_orchestrator()
        if not orchestrator:
            raise HTTPException(status_code=500, detail="Orchestrator not initialized")
        
        # Get the agent
        agent = orchestrator.get_agent(request.agent_name)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent not found: {request.agent_name}")
        
        # Generate document
        doc_info = await agent.generate_document(
            template_name=request.template_name,
            data=request.data,
            doc_type=request.doc_type,
            filename=request.filename,
            format=request.format,
            metadata=request.metadata
        )
        
        # Store document info in memory
        background_tasks.add_task(
            orchestrator.memory_manager.store_agent_memory,
            agent_name=request.agent_name,
            memory_type="document",
            content=doc_info,
            is_shared=True,
            confidence=0.9
        )
        
        return {
            "status": "success",
            "document": doc_info,
            "agent": request.agent_name
        }
    except Exception as e:
        logger.error(f"Failed to generate document: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate document: {str(e)}")

@router.get("/download/{doc_type}/{filename}")
async def download_document(doc_type: str, filename: str):
    """Download a generated document"""
    try:
        import os
        from fastapi.responses import FileResponse
        
        # Ensure filename has an extension
        if "." not in filename:
            filename += ".pdf"  # Default to PDF
        
        file_path = os.path.join("./data/documents", doc_type, filename)
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"Document not found: {filename}")
        
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type="application/octet-stream"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download document: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to download document: {str(e)}")

@router.get("/list")
async def list_documents(doc_type: Optional[str] = None):
    """List available documents"""
    try:
        import os
        from pathlib import Path
        
        documents = []
        base_dir = Path("./data/documents")
        
        if doc_type:
            # List documents of specific type
            doc_dir = base_dir / doc_type
            if not doc_dir.exists():
                return {"documents": []}
            
            for file_path in doc_dir.glob("*.*"):
                documents.append({
                    "name": file_path.name,
                    "path": f"{doc_type}/{file_path.name}",
                    "type": doc_type,
                    "size": file_path.stat().st_size,
                    "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                })
        else:
            # List all documents
            for doc_dir in base_dir.iterdir():
                if doc_dir.is_dir():
                    type_name = doc_dir.name
                    for file_path in doc_dir.glob("*.*"):
                        documents.append({
                            "name": file_path.name,
                            "path": f"{type_name}/{file_path.name}",
                            "type": type_name,
                            "size": file_path.stat().st_size,
                            "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                        })
        
        return {"documents": documents}
    except Exception as e:
        logger.error(f"Failed to list documents: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")

@router.delete("/delete/{doc_type}/{filename}")
async def delete_document(doc_type: str, filename: str):
    """Delete a document"""
    try:
        import os
        from pathlib import Path
        
        file_path = Path(f"./data/documents/{doc_type}/{filename}")
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"Document not found: {filename}")
        
        file_path.unlink()
        return {"status": "success", "message": f"Document deleted: {filename}"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete document: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")

# Scheduled document generation (to be implemented with APScheduler)
@router.post("/schedule")
async def schedule_document_generation(request: ScheduledDocumentRequest):
    """Schedule periodic document generation"""
    # This is a placeholder - will be implemented when we add APScheduler
    return {
        "status": "not_implemented",
        "message": "Scheduled document generation will be implemented in the next phase"
    }