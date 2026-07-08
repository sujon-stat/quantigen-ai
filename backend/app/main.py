from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os
from backend.app.api.router import api_router
from backend.app.core.exceptions import StatMindException, StatMindErrorLevel
from backend.app.services.session.manager import session_manager

app = FastAPI(
    title="Quantigen AI — No-Code Statistical Analysis Platform",
    version="1.0.0",
    description="Backend REST API powering Quantigen AI: assumption checking, method execution, educational explanations, and transparent code generation."
)

# Configure CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(StatMindException)
async def statmind_exception_handler(request: Request, exc: StatMindException):
    """Translate custom StatMind exceptions into structured 5-level educational JSON payloads."""
    status_code = 400
    if exc.level == StatMindErrorLevel.ASSUMPTION_VIOLATION:
        status_code = 422
    elif exc.level == StatMindErrorLevel.SYSTEM_ERROR:
        status_code = 500
    elif exc.level == StatMindErrorLevel.INFO or exc.level == StatMindErrorLevel.WARNING:
        status_code = 200

    return JSONResponse(
        status_code=status_code,
        content={
            "status": "error",
            "error_code": exc.error_code,
            "level": exc.level.value,
            "title": exc.translation.get("title", "Error"),
            "message": exc.translation.get("message", str(exc)),
            "action": exc.translation.get("action", "Please verify your dataset or settings."),
            "icon": exc.translation.get("icon", "alert-circle")
        }
    )


@app.get("/api/v1/health", status_code=200, tags=["system"])
async def health_check():
    """System health check endpoint reporting active session status."""
    active_datasets = session_manager.list_datasets()
    return {
        "status": "ok",
        "service": "Quantigen AI Backend API",
        "version": "1.0.0",
        "active_datasets_count": len(active_datasets)
    }


# Include main API router
app.include_router(api_router, prefix="/api/v1")


# Mount Static Assets & SPA Fallback for Universal Single-Server Deployment
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DIST_DIR = os.path.join(PROJECT_ROOT, "frontend", "dist")
ASSETS_DIR = os.path.join(DIST_DIR, "assets")

if os.path.exists(ASSETS_DIR):
    app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")


@app.get("/{full_path:path}", include_in_schema=False)
async def serve_spa_or_static(full_path: str):
    """Serve built static frontend SPA when not matching API endpoints."""
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API endpoint not found")
    
    if not os.path.exists(DIST_DIR):
        return JSONResponse(
            status_code=503,
            content={"message": "Quantigen AI API online. Frontend production build not found on disk. Run `npm run build` inside `frontend/`."}
        )
    
    file_path = os.path.join(DIST_DIR, full_path)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(file_path)
    
    # Return index.html for Single Page Application routing
    index_path = os.path.join(DIST_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return JSONResponse(status_code=404, content={"message": "Frontend index.html not found."})
