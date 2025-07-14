"""
Main API entry point for AgentFlow
"""
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import controllers
from api.auth_controller import router as auth_router
from api.health_controller import router as health_router
from api.workflow_controller import router as workflow_router
from api.enhanced_controller import router as enhanced_router

# Create FastAPI app
app = FastAPI(
    title="AgentFlow API",
    description="API for AgentFlow - AI Agent Orchestration Platform",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(workflow_router)
app.include_router(enhanced_router)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "AgentFlow API",
        "version": "1.0.0",
        "status": "running"
    }

if __name__ == "__main__":
    # Get port from environment or use default
    port = int(os.getenv("PORT", 8000))
    
    # Run server
    uvicorn.run("api.main:app", host="0.0.0.0", port=port, reload=True)