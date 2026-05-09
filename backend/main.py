from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from database import engine, Base
from routers.auth import router as auth_router
from routers.polls import router as polls_router

app = FastAPI(title="Voting API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(polls_router)


@app.get("/health")
def health():
    return {"code": 200, "message": "ok", "data": "Voting API is running"}


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


frontend_path = Path(__file__).parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="frontend")
