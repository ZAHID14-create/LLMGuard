from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

try:
    from app.core.config import settings
    from app.api.endpoints import router as api_router
except ImportError:
    from backend.app.core.config import settings
    from backend.app.api.endpoints import router as api_router

# Initialize FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.API_VERSION,
    description="Backend API for LLMGuard – AI Evaluation & Safety Monitoring Platform",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure Cross-Origin Resource Sharing (CORS) for Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API endpoints under /api prefix
app.include_router(api_router, prefix="/api")


@app.get("/", tags=["Root"])
def root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "status": "online",
        "documentation": "/docs",
        "health_endpoint": "/api/health",
        "info_endpoint": "/api/info",
        "chat_endpoint": "/api/chat",
        "metrics_endpoint": "/api/metrics",
    }
