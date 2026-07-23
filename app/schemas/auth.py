from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(min_length=8)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8)


# Used by the OTP-based password reset flow (forgot_password → reset via OTP code)
class ResetPasswordOTPRequest(BaseModel):
    email: EmailStr
    otp_code: str = Field(..., min_length=4, max_length=4)
    password: str = Field(..., min_length=8)
