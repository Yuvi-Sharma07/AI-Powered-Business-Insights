from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routers import entities, analytics
from app.config import settings

# Auto-create database tables on startup (ideal for local SQLite setup)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI-Powered Business Insights API",
    description="Backend API for Sales Analytics, Anomaly Detection, and Natural Language Querying.",
    version="1.0.0"
)

# Add CORS Middleware to enable smooth frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for development; restrict in production environments
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Routers
app.include_router(entities.router, prefix="/api", tags=["Entities"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics & AI"])

@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "AI-Powered Business Insights API",
        "documentation": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=True)
