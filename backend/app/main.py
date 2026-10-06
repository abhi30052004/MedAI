from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.workers.worker import start_worker, stop_worker

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start background worker
    start_worker()
    yield
    # Shutdown: Stop worker
    stop_worker()


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI-powered medical case analysis and clinical workflow assistance.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
origins = [
    settings.FRONTEND_URL,
    "http://localhost:5173",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root route
@app.get("/")
def read_root():
    return {"message": f"Welcome to {settings.PROJECT_NAME}"}

@app.get("/health")
def health_check():
    return {"status": "ok"}

# ── Routers ───────────────────────────────────────────────────────
from app.api.auth import router as auth_router
app.include_router(auth_router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])

from app.api.users import router as users_router
app.include_router(users_router, prefix=f"{settings.API_V1_STR}/users", tags=["users"])

from app.api.org import router as org_router
app.include_router(org_router, prefix=f"{settings.API_V1_STR}/org", tags=["org"])

from app.api.teams import router as teams_router
app.include_router(teams_router, prefix=f"{settings.API_V1_STR}/teams", tags=["teams"])

from app.api.patients import router as patients_router
app.include_router(patients_router, prefix=f"{settings.API_V1_STR}/patients", tags=["patients"])

from app.api.cases import router as cases_router
app.include_router(cases_router, prefix=f"{settings.API_V1_STR}/cases", tags=["cases"])

from app.api.documents import router as documents_router
# Note: document routes don't have a prefix here, they are mounted inside
app.include_router(documents_router, prefix=f"{settings.API_V1_STR}", tags=["documents"])

from app.api.analysis import router as analysis_router
app.include_router(analysis_router, prefix=f"{settings.API_V1_STR}", tags=["analysis"])

from app.api.audit import router as audit_router
app.include_router(audit_router, prefix=f"{settings.API_V1_STR}/audit-logs", tags=["audit"])
