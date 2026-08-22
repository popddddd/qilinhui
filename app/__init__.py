import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app import database

BASE_DIR = Path(__file__).resolve().parent.parent

app = FastAPI(title="麒麟汇 · 量化交易 Demo")
app.secret_key = os.environ.get("SESSION_SECRET", "qilinhui-demo-secret-key-change-me")

database.init_db()

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "app" / "static")), name="static")

from app.auth import router as auth_router

app.include_router(auth_router)