from dotenv import load_dotenv
# Load environment variables from .env file
load_dotenv(override=True)

import sys
import asyncio

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:
        import uvicorn.loops.asyncio as uv_asyncio
        uv_asyncio.asyncio_loop_factory = lambda use_subprocess=False: asyncio.SelectorEventLoop
    except ImportError:
        pass

from typing import Annotated
from fastapi import Depends, FastAPI, Request, HTTPException, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException
import app.models
from app.database import Base, engine, get_db

from app.routers.auth_router import router as auth_router
from app.routers.user_router import router as user_router
from app.routers.chat_router import router as chat_router

import time
from datetime import datetime

# khởi tạo đối tượng API làm trung tâm gán các đường dẫn 
app = FastAPI()

@app.middleware("http")
async def log_requests(request: Request, call_next):
    method = request.method
    path = request.url.path
    # Write to logs/debug.log
    try:
        with open("logs/debug.log", "a", encoding="utf-8") as f:
            f.write(f"{datetime.now().isoformat()} - [Middleware] Incoming: {method} {path}\n")
    except Exception:
        pass
        
    start_time = time.time()
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        try:
            with open("logs/debug.log", "a", encoding="utf-8") as f:
                f.write(f"{datetime.now().isoformat()} - [Middleware] Response: {method} {path} status={response.status_code} latency={process_time:.2f}s\n")
        except Exception:
            pass
        return response
    except Exception as e:
        process_time = time.time() - start_time
        try:
            with open("logs/debug.log", "a", encoding="utf-8") as f:
                f.write(f"{datetime.now().isoformat()} - [Middleware] Exception: {method} {path} error={str(e)} latency={process_time:.2f}s\n")
        except Exception:
            pass
        raise e

# Đăng ký các router
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(chat_router)

from pydantic import BaseModel

class DebugLogPayload(BaseModel):
    message: str
    source: str | None = None
    lineno: int | None = None
    colno: int | None = None
    stack: str | None = None

@app.post("/api/debug/log", include_in_schema=False)
async def debug_log_browser(payload: DebugLogPayload):
    try:
        with open("logs/debug.log", "a", encoding="utf-8") as f:
            f.write(
                f"{datetime.now().isoformat()} - [BROWSER ERROR] {payload.message} "
                f"at {payload.source}:{payload.lineno}:{payload.colno}\n"
            )
            if payload.stack:
                f.write(f"Stack Trace:\n{payload.stack}\n")
    except Exception:
        pass
    return {"status": "ok"}

# gán mount để quản lý file tĩnh
# tham số 1 tượng trưng cho đường dẫn trên url 
# tham số 2 là thư mục static trong project
# tham số 3 là tên đặt cho cấu hình này(tên này dùng để nhúng trong file html)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/media", StaticFiles(directory="media"), name="media")

# tìm các file trong thư mục templates rồi gán cho biến template
templates = Jinja2Templates(directory="templates")


@app.get("/", include_in_schema=False, name="home")
@app.get("/home01", include_in_schema=False, name="home01")
async def home(request: Request):
    return templates.TemplateResponse(
        request,
        "home.html",
        {"title": "Trang chủ"},
    )

@app.get("/login", include_in_schema=False, name="login")
async def login_page(request: Request):
    return templates.TemplateResponse(
        request,
        "login.html",
        {"title": "Đăng nhập"},
    )

@app.get("/register", include_in_schema=False, name="register")
async def register_page(request: Request):
    return templates.TemplateResponse(
        request,
        "register.html",
        {"title": "Đăng ký"},
    )


@app.exception_handler(StarletteHTTPException)
def general_http_exception_handler(request: Request, exception: StarletteHTTPException):
    # khởi tạo msg
    message = (
        #msg chi tiết về lỗi 
        exception.detail
        # nếu có lỗi trong phạm vi của mã lỗi thì trả lỗi đó
        if exception.detail
        # nếu không trong phạm vi thì trả về dòng dưới
        else "An error occurred. Please check your request and try again."
    )
    # lỗi riêng dành cho frontend/mobile
    if request.url.path.startswith("/api"):
        # trả về định dạng json
        return JSONResponse(
            status_code=exception.status_code,
            content={"detail": message},
        )
    # lỗi dành cho người dùng web trả về html trực quan
    return templates.TemplateResponse(
        request,
        "error.html",
        {
            # các tham số sẽ được truyền vào file error
            "status_code": exception.status_code,
            "title": exception.status_code,
            "message": message,
        },
        status_code=exception.status_code,
    )
@app.exception_handler(RequestValidationError)
def validation_exception_handler(request: Request, exception: RequestValidationError):
    if request.url.path.startswith("/api"):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={"detail": exception.errors()},
        )
    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "status_code": status.HTTP_422_UNPROCESSABLE_CONTENT,
            "title": status.HTTP_422_UNPROCESSABLE_CONTENT,
            "message": "Invalid request. Please check your input and try again.",
        },
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
    )
