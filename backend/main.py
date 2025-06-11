import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from dotenv import load_dotenv

from routers.document_routes import router as document_router

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting Document Extraction API")
    
    # Create necessary directories
    upload_dir = os.getenv("UPLOAD_DIR", "./uploads")
    storage_dir = os.getenv("STORAGE_DIR", "./storage")
    os.makedirs(upload_dir, exist_ok=True)
    os.makedirs(storage_dir, exist_ok=True)
    
    yield
    
    # Shutdown
    logger.info("Shutting down Document Extraction API")


# Create FastAPI app
app = FastAPI(
    title="Agentic Document Extraction API",
    description="Multi-agent document extraction platform with visual grounding",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(document_router)

# Serve static files (for uploaded documents if needed)
upload_dir = os.getenv("UPLOAD_DIR", "./uploads")
if os.path.exists(upload_dir):
    app.mount("/uploads", StaticFiles(directory=upload_dir), name="uploads")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Agentic Document Extraction API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health"
    }


@app.get("/api/info")
async def api_info():
    """API information endpoint"""
    return {
        "name": "Agentic Document Extraction API",
        "version": "1.0.0",
        "description": "Multi-agent document extraction platform with LangGraph",
        "supported_formats": ["PDF", "PNG", "JPEG"],
        "features": [
            "Multi-agent processing workflow",
            "Visual grounding with bounding boxes",
            "Hierarchical data extraction",
            "Human-in-the-loop validation",
            "Real-time processing status"
        ],
        "endpoints": {
            "upload": "POST /api/upload",
            "status": "GET /api/status/{transaction_id}",
            "result": "GET /api/result/{transaction_id}",
            "grounding": "GET /api/grounding/{chunk_id}",
            "corrections": "PATCH /api/correct/{transaction_id}",
            "page_image": "GET /api/page-image/{transaction_id}",
            "health": "GET /api/health"
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )
