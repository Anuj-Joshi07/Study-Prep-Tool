"""
Study Prep Tool — FastAPI application entry point.
"""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import init_db

from app.routers.students import router as students_router
from app.routers.chat import router as chat_router
from app.routers.documents import router as documents_router
from app.routers.quiz import router as quiz_router
from app.routers.resume import router as resume_router
from app.routers.roadmap import router as roadmap_router
from app.routers.interview import router as interview_router
from app.routers.dashboard import router as dashboard_router

Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
Path(settings.CHROMA_DB_PATH).mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    print(f"\n✅  {settings.APP_NAME} v{settings.APP_VERSION} started")
    print(f"   LLM   : {settings.LLM_PROVIDER} → {settings.GROQ_MODEL_CHAT}")
    print(f"   DB    : {settings.DATABASE_URL}")
    print(f"   Docs  : http://localhost:8000/docs\n")
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Unified AI learning & career platform.",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(students_router)
app.include_router(chat_router)
app.include_router(documents_router)
app.include_router(quiz_router)
app.include_router(resume_router)
app.include_router(roadmap_router)
app.include_router(interview_router)
app.include_router(dashboard_router)


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}


@app.get("/", tags=["Health"])
def root():
    return {"message": f"Welcome to {settings.APP_NAME}!", "docs": "/docs"}


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "type": type(exc).__name__},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
