import time
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError

from app import database
from app.models import LoginRequest, RegisterRequest
from app.utils import (
    create_session,
    destroy_session,
    get_current_user,
    hash_password,
    verify_password,
)

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

FAILED_LOGIN_LIMIT = 3
FAILED_LOGIN_WINDOW_SECONDS = 600
_failed_logins: dict[str, list[float]] = {}


def _record_failure(username: str) -> None:
    now = time.time()
    recent = [t for t in _failed_logins.get(username, []) if now - t < FAILED_LOGIN_WINDOW_SECONDS]
    recent.append(now)
    _failed_logins[username] = recent


def _too_many_failures(username: str) -> bool:
    now = time.time()
    recent = [t for t in _failed_logins.get(username, []) if now - t < FAILED_LOGIN_WINDOW_SECONDS]
    return len(recent) >= FAILED_LOGIN_LIMIT


def _clear_failures(username: str) -> None:
    _failed_logins.pop(username, None)


def _login_failed() -> RedirectResponse:
    return RedirectResponse(url="/login?error=1", status_code=303)


def _register_error(request: Request, error: str, values: dict) -> HTMLResponse:
    return templates.TemplateResponse(request, "register.html", {"error": error, "form": values})


def _format_register_errors(exc: ValidationError) -> str:
    for err in exc.errors():
        loc = err.get("loc", [])
        if "email" in loc:
            return "邮箱格式不正确"
        if "password" in loc:
            return "密码长度不能少于 6 位"
        if "username" in loc:
            return "用户名不能为空（且不超过 50 个字符）"
    return "提交内容有误，请检查后重试"


@router.get("/", response_class=HTMLResponse)
async def index() -> RedirectResponse:
    return RedirectResponse(url="/login")


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "register.html", {"error": None, "form": {}})


@router.post("/register", response_class=HTMLResponse)
async def register(request: Request) -> HTMLResponse:
    form = await request.form()
    values = {
        "username": str(form.get("username", "")).strip(),
        "email": str(form.get("email", "")).strip(),
        "password": str(form.get("password", "")),
    }
    confirm_password = str(form.get("confirm_password", ""))

    try:
        data = RegisterRequest(**values)
    except ValidationError as exc:
        return _register_error(request, _format_register_errors(exc), values)

    if data.password != confirm_password:
        return _register_error(request, "两次输入的密码不一致", values)
    if database.get_user_by_username(data.username):
        return _register_error(request, "该用户名已被注册", values)
    if database.get_user_by_email(data.email):
        return _register_error(request, "该邮箱已被注册", values)

    database.create_user(data.username, data.email, hash_password(data.password))
    return RedirectResponse(url="/login?registered=true", status_code=303)


@router.get("/login", response_class=HTMLResponse)
async def login_page(
    request: Request, registered: Optional[str] = None, error: Optional[str] = None
) -> HTMLResponse:
    if get_current_user(request):
        return RedirectResponse(url="/dashboard")
    return templates.TemplateResponse(
        request,
        "login.html",
        {"registered": registered == "true", "error": error is not None},
    )


@router.post("/login", response_class=HTMLResponse)
async def login(request: Request) -> HTMLResponse:
    form = await request.form()
    remember = str(form.get("remember", "")) in ("1", "true", "on")
    try:
        data = LoginRequest(
            username=str(form.get("username", "")).strip(),
            password=str(form.get("password", "")),
        )
    except ValidationError:
        return _login_failed()

    if _too_many_failures(data.username):
        return _login_failed()

    user = database.get_user_by_username(data.username)
    if user is None or not verify_password(data.password, user["hashed_password"]):
        _record_failure(data.username)
        return _login_failed()

    _clear_failures(data.username)
    token, max_age = create_session(data.username, remember)
    response = RedirectResponse(url="/dashboard", status_code=303)
    response.set_cookie(
        key="session",
        value=token,
        max_age=max_age,
        httponly=True,
        samesite="lax",
    )
    return response


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request) -> HTMLResponse:
    username = get_current_user(request)
    if username is None:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse(request, "dashboard.html", {"username": username})


@router.get("/logout")
async def logout(request: Request) -> RedirectResponse:
    destroy_session(request)
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie(key="session")
    return response