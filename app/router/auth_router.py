from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field, EmailStr
import os
import random
import smtplib
from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from starlette.concurrency import run_in_threadpool
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from datasabe import get_db
from models.user import User
from schemas.user import ProfileUpdate
from schemas.user import UserCreate, UserResponse
from schemas.auth import LoginRequest
from app.auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_active_user,
)

# In-memory OTP store: {email: {"code": otp_code, "expires_at": datetime}}
otp_store = {}

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordOTPRequest(BaseModel):
    email: EmailStr
    otp_code: str = Field(..., min_length=4, max_length=4)
    password: str = Field(..., min_length=8)

def send_email_sync(to_email: str, subject: str, html_content: str):
    smtp_host = os.getenv("MAIL_HOST", "sandbox.smtp.mailtrap.io")
    try:
        smtp_port = int(os.getenv("MAIL_PORT", "2525"))
    except ValueError:
        smtp_port = 2525
        
    smtp_username = os.getenv("MAIL_USERNAME")
    smtp_password = os.getenv("MAIL_PASSWORD")
    from_email = os.getenv("MAIL_FROM", "noreply@netai.com")
    from_name = os.getenv("MAIL_FROM_NAME", "NetAI Portal")
    
    if not smtp_username or not smtp_password:
        raise Exception("Cấu hình Mailtrap SMTP (MAIL_USERNAME/MAIL_PASSWORD) chưa được thiết lập trong file .env.")
        
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{from_name} <{from_email}>"
    msg["To"] = to_email
    
    part = MIMEText(html_content, "html", "utf-8")
    msg.attach(part)
    
    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.sendmail(from_email, to_email, msg.as_string())

async def send_otp_email(to_email: str, otp_code: str):
    subject = f"Mã xác thực khôi phục mật khẩu: {otp_code}"
    html_content = f"""
    <html>
        <body style="font-family: 'Segoe UI', Arial, sans-serif; background-color: #0b0f19; color: #f3f4f6; padding: 20px;">
            <div style="max-width: 500px; margin: 0 auto; background-color: #111827; border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 30px; text-align: center; box-shadow: 0 4px 15px rgba(0,0,0,0.5);">
                <h2 style="color: #E100FF; margin-bottom: 10px; font-weight: bold;">NetAI Portal</h2>
                <p style="color: #9ca3af; font-size: 16px; margin-bottom: 20px;">Bạn đã yêu cầu khôi phục mật khẩu. Dưới đây là mã xác thực (OTP) gồm 4 chữ số của bạn:</p>
                <div style="font-size: 36px; font-weight: bold; letter-spacing: 5px; color: #00C6FF; margin: 20px 0; padding: 15px; background-color: rgba(0,0,0,0.3); border-radius: 8px; display: inline-block;">
                    {otp_code}
                </div>
                <p style="color: #9ca3af; font-size: 14px; margin-top: 20px;">Mã này có hiệu lực trong vòng 5 phút. Vui lòng không chia sẻ mã này với bất kỳ ai.</p>
                <hr style="border: 0; border-top: 1px solid rgba(255,255,255,0.08); margin: 20px 0;">
                <p style="color: #6b7280; font-size: 12px;">Nếu bạn không yêu cầu thay đổi này, hãy bỏ qua email này.</p>
            </div>
        </body>
    </html>
    """
    await run_in_threadpool(send_email_sync, to_email, subject, html_content)


router = APIRouter(prefix="/api/auth", tags=["Authentication"])



@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user."""
    # Check if username already exists
    username_check = await db.execute(select(User).where(User.username == user_data.username))
    if username_check.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tên người dùng đã được đăng ký."
        )

    # Check if email already exists
    email_check = await db.execute(select(User).where(User.email == user_data.email))
    if email_check.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="đã có tài khoản đăng ký với gmail bạn vừa nhập"
        )

    # Create new user
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=hash_password(user_data.password),
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

@router.post("/login")
async def login(login_data: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Login and return JWT access token for LocalStorage storage."""
    # Find user by email
    result = await db.execute(select(User).where(User.email == login_data.email))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email hoặc mật khẩu không chính xác."
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tài khoản này đã bị khóa."
        )

    # Create JWT token
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return {
        "success": True,
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
        }
    }

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_active_user)):
    """Get current authenticated user info."""
    return current_user

@router.put("/me", response_model=UserResponse)
async def update_profile(
    update_data: ProfileUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update current user's full name and/or password."""
    if update_data.full_name is not None:
        current_user.full_name = update_data.full_name
        
    if update_data.password is not None:
        current_user.hashed_password = hash_password(update_data.password)
        
    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)
    return current_user

@router.post("/forgot-password")
async def forgot_password(req_data: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Request a password reset OTP code."""
    # Find user by email
    result = await db.execute(select(User).where(User.email == req_data.email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy tài khoản với email này."
        )
        
    # Generate 4-digit OTP
    otp_code = f"{random.randint(1000, 9999)}"
    
    # Store in otp_store
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
    otp_store[req_data.email] = {
        "code": otp_code,
        "expires_at": expires_at
    }
    
    # Send email
    try:
        await send_otp_email(req_data.email, otp_code)
    except Exception as e:
        print(f"Error sending email: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi gửi email: {str(e)}"
        )
        
    return {
        "success": True,
        "message": "Mã xác thực OTP đã được gửi đến email của bạn."
    }

@router.post("/reset-password")
async def reset_password(req_data: ResetPasswordOTPRequest, db: AsyncSession = Depends(get_db)):
    """Verify OTP code and reset password."""
    email = req_data.email
    
    # Verify OTP
    if email not in otp_store:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Yêu cầu đặt lại mật khẩu không hợp lệ hoặc đã hết hạn."
        )
        
    store_data = otp_store[email]
    if store_data["code"] != req_data.otp_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mã xác thực không chính xác."
        )
        
    if datetime.now(timezone.utc) > store_data["expires_at"]:
        # Delete expired OTP
        otp_store.pop(email, None)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mã xác thực đã hết hạn (hết hiệu lực sau 5 phút)."
        )
        
    # Retrieve user
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy tài khoản với email này."
        )
        
    # Update password
    user.hashed_password = hash_password(req_data.password)
    db.add(user)
    await db.commit()
    
    # Remove OTP from store
    otp_store.pop(email, None)
    
    return {
        "success": True,
        "message": "Đặt lại mật khẩu thành công! Bạn có thể đăng nhập bằng mật khẩu mới."
    }
