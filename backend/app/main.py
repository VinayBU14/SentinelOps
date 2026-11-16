from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from app.core.config import settings
from app.core.errors import SentinelOpsException
from app.db.init_db import init_db
from app.api.v1.uploads import router as uploads_router
from app.api.v1.batches import router as batches_router
from app.api.v1.assets import router as assets_router
from app.api.v1.issues import router as issues_router
from app.api.v1.risks import router as risks_router

# Initialize database schema on startup
init_db()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Cyber Asset Inventory and Explainable Risk Analysis API",
    version="1.0.0",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom exception handler
@app.exception_handler(SentinelOpsException)
async def sentinelops_exception_handler(request: Request, exc: SentinelOpsException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

# Include routers
app.include_router(uploads_router, prefix=settings.API_V1_STR)
app.include_router(batches_router, prefix=settings.API_V1_STR)
app.include_router(assets_router, prefix=settings.API_V1_STR)
app.include_router(issues_router, prefix=settings.API_V1_STR)
app.include_router(risks_router, prefix=settings.API_V1_STR)

@app.get(f"{settings.API_V1_STR}/sample-dataset", tags=["System"])
def get_sample_dataset():
    """Safely serve the official AegisCorp sample inventory CSV."""
    candidates = [
        Path("datasets/aegiscorp_asset_inventory_1200.csv"),
        Path("aegiscorp_asset_inventory_1200.csv"),
    ]
    for path in candidates:
        if path.exists():
            return FileResponse(
                path=str(path),
                filename="aegiscorp_asset_inventory_1200.csv",
                media_type="text/csv"
            )
    raise HTTPException(status_code=404, detail="Sample dataset file not found.")

@app.get(f"{settings.API_V1_STR}/health", tags=["System"])
def health_check():
    return {
        "status": "ok",
        "service": settings.PROJECT_NAME,
        "version": "1.0.0"
    }

# Mount built frontend static files if available
frontend_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if frontend_dist.exists() and (frontend_dist / "index.html").exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")
else:
    @app.get("/", tags=["Root"])
    def root():
        return {
            "message": "SentinelOps API is running. Access API documentation at /docs",
            "health": f"{settings.API_V1_STR}/health"
        }

