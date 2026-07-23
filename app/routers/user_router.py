from fastapi import APIRouter, Request, Depends, HTTPException, status, UploadFile, File
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool
import io
from PIL import Image

from app.database import get_db
from app.models.user import User
from app.schemas.user import UserResponse
from app.auth import get_current_active_user
from app.config import settings
from app.services.image_service import process_profile_image, delete_profile_image

router = APIRouter(tags=["User Profile Views & Actions"])
templates = Jinja2Templates(directory="templates")


@router.get("/account", include_in_schema=False, name="account")
async def account_page(request: Request):
    return templates.TemplateResponse(
        request,
        "account.html",
        {"title": "Tài khoản của tôi"},
    )


@router.get("/forgot-password", include_in_schema=False, name="forgot_password")
async def forgot_password_page(request: Request):
    return templates.TemplateResponse(
        request,
        "forgot_password.html",
        {"title": "Quên mật khẩu"},
    )


@router.post("/api/auth/avatar", response_model=UserResponse)
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload user avatar and replace the old one if it exists."""
    # 1. Read file content
    content = await file.read()
    
    # 2. Check file size
    if len(content) > settings.max_upload_size_bytes:
        max_size_mb = settings.max_upload_size_bytes / (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Kích thước ảnh vượt quá giới hạn cho phép ({max_size_mb:.1f} MB)."
        )
        
    # 3. Validate image file format using Pillow
    try:
        img = Image.open(io.BytesIO(content))
        img.verify()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tệp tải lên không phải là định dạng hình ảnh hợp lệ."
        )
        
    # 4. Save the new image and get the saved filename
    try:
        filename = await run_in_threadpool(process_profile_image, content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Không thể xử lý hình ảnh: {str(e)}"
        )
        
    # 5. Delete old image from system if it exists
    old_avatar = current_user.avatar_url
    if old_avatar:
        try:
            await run_in_threadpool(delete_profile_image, old_avatar)
        except Exception as e:
            print(f"Lỗi khi xóa ảnh đại diện cũ: {e}")
            
    # 6. Update user avatar_url in the database
    current_user.avatar_url = filename
    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)
    
    return current_user


@router.get("/chat", include_in_schema=False, name="chat")
async def chat_page(request: Request):
    return templates.TemplateResponse(
        request,
        "chat.html",
        {"title": "Trợ lý AI"},
    )
