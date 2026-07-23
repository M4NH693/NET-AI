from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field, EmailStr
import random
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from app.database import get_db
from app.models.user import User
from app.schemas.user import ProfileUpdate, UserCreate, UserResponse
from app.schemas.auth import LoginRequest, ResetPasswordOTPRequest, ForgotPasswordRequest as ForgotPasswordRequestSchema
from app.auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_active_user,
)
from app.services.email_service import send_otp_email

# In-memory OTP store: {email: {"code": otp_code, "expires_at": datetime}}
otp_store = {}

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
async def forgot_password(req_data: ForgotPasswordRequestSchema, db: AsyncSession = Depends(get_db)):
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
