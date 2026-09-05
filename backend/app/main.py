from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.routes import alerts, applications, auth, interviews, jobs, dashboard, users

app = FastAPI(title="RecruitFlow API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    # WHY allow_credentials=True: our auth cookie must be sent cross-origin
    # from the Vite dev server (port 5173) to the API (port 8000), and later
    # from the deployed frontend domain to the deployed backend domain.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(jobs.router)
app.include_router(applications.router)
app.include_router(interviews.router)
app.include_router(dashboard.router)
app.include_router(alerts.router)
app.include_router(users.router)


@app.get("/")
def root():
    return {
        "status": "online",
        "message": "RecruitFlow API is running",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health():
    return {"status": "ok"}
