"""
Authentication API Endpoints.

Provides REST endpoints for:
- User registration
- Login/logout
- Token refresh
- Password management
- Email verification
"""

from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, EmailStr, Field, ConfigDict

from app.db import UnitOfWork, get_uow, get_current_user
from app.db.models_auth import User
from app.services.auth import AuthService


router = APIRouter(prefix="/auth", tags=["Authentication"])


# =============================================================================
# REQUEST/RESPONSE SCHEMAS
# =============================================================================

class RegisterRequest(BaseModel):
    """User registration request."""
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    display_name: str = Field(min_length=1, max_length=100)


class LoginRequest(BaseModel):
    """Login request."""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_at: datetime


class RefreshRequest(BaseModel):
    """Token refresh request."""
    refresh_token: str


class PasswordChangeRequest(BaseModel):
    """Password change request (authenticated)."""
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)


class PasswordResetRequest(BaseModel):
    """Password reset request (forgot password)."""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation."""
    token: str
    new_password: str = Field(min_length=8, max_length=128)


class EmailVerificationRequest(BaseModel):
    """Email verification request."""
    token: str


class ResendVerificationRequest(BaseModel):
    """Resend verification email request."""
    email: EmailStr


class UserResponse(BaseModel):
    """User response (public info)."""
    id: str
    email: str
    display_name: str
    email_verified: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MessageResponse(BaseModel):
    """Simple message response."""
    message: str
    success: bool = True


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_client_ip(request: Request) -> Optional[str]:
    """Extract client IP from request."""
    # Check for forwarded header (behind proxy)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


def get_user_agent(request: Request) -> Optional[str]:
    """Extract user agent from request."""
    return request.headers.get("User-Agent")


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    data: RegisterRequest,
    request: Request,
    uow: UnitOfWork = Depends(get_uow),
):
    """
    Register a new user.

    Returns the created user. A verification email will be sent
    to the provided email address.
    """
    auth = AuthService(uow)

    result = await auth.register(
        email=data.email,
        password=data.password,
        display_name=data.display_name,
        ip_address=get_client_ip(request),
        require_email_verification=True,
    )

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.error or "Registration failed"
        )

    await uow.commit()

    # TODO: Send verification email with result.verification_token
    # For now, just return the user

    return UserResponse(
        id=str(result.user.id),
        email=result.user.email,
        display_name=result.user.display_name,
        email_verified=result.user.email_verified,
        created_at=result.user.created_at,
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest,
    request: Request,
    uow: UnitOfWork = Depends(get_uow),
):
    """
    Login with email and password.

    Returns access and refresh tokens.
    """
    auth = AuthService(uow)

    result = await auth.login(
        email=data.email,
        password=data.password,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        require_verified_email=False,  # Set to True in production
    )

    if not result.success:
        if result.requires_verification:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Email verification required"
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=result.error or "Invalid credentials"
        )

    await uow.commit()

    return TokenResponse(
        access_token=result.tokens.access_token,
        refresh_token=result.tokens.refresh_token,
        token_type=result.tokens.token_type,
        expires_at=result.tokens.access_token_expires,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_tokens(
    data: RefreshRequest,
    request: Request,
    uow: UnitOfWork = Depends(get_uow),
):
    """
    Refresh access token using refresh token.

    The old refresh token is invalidated and a new one is issued.
    """
    auth = AuthService(uow)

    result = await auth.refresh_tokens(
        refresh_token=data.refresh_token,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
    )

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=result.error or "Invalid refresh token"
        )

    await uow.commit()

    return TokenResponse(
        access_token=result.tokens.access_token,
        refresh_token=result.tokens.refresh_token,
        token_type=result.tokens.token_type,
        expires_at=result.tokens.access_token_expires,
    )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    data: RefreshRequest,
    request: Request,
    uow: UnitOfWork = Depends(get_uow),
):
    """
    Logout by revoking the refresh token.

    The access token remains valid until it expires,
    but the refresh token can no longer be used.
    """
    auth = AuthService(uow)

    await auth.logout(
        refresh_token=data.refresh_token,
        ip_address=get_client_ip(request),
    )

    await uow.commit()

    return MessageResponse(message="Successfully logged out")


@router.post("/logout-all", response_model=MessageResponse)
async def logout_all_devices(
    request: Request,
    uow: UnitOfWork = Depends(get_uow),
    current_user: User = Depends(get_current_user),
):
    """
    Logout from all devices.

    Revokes all refresh tokens for the current user.
    """
    auth = AuthService(uow)

    count = await auth.logout_all_devices(
        user_id=current_user.id,
        ip_address=get_client_ip(request),
    )

    await uow.commit()

    return MessageResponse(message=f"Logged out from {count} device(s)")


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
):
    """Get current user information."""
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        display_name=current_user.display_name,
        email_verified=current_user.email_verified,
        created_at=current_user.created_at,
    )


@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    data: PasswordChangeRequest,
    request: Request,
    uow: UnitOfWork = Depends(get_uow),
    current_user: User = Depends(get_current_user),
):
    """
    Change password (authenticated user).

    Requires current password for verification.
    """
    auth = AuthService(uow)

    result = await auth.change_password(
        user_id=current_user.id,
        current_password=data.current_password,
        new_password=data.new_password,
        ip_address=get_client_ip(request),
    )

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.error or "Password change failed"
        )

    await uow.commit()

    return MessageResponse(message="Password changed successfully")


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    data: PasswordResetRequest,
    request: Request,
    uow: UnitOfWork = Depends(get_uow),
):
    """
    Request password reset.

    If the email exists, a reset token will be generated.
    For security, always returns success even if email doesn't exist.
    """
    auth = AuthService(uow)

    exists, token = await auth.request_password_reset(
        email=data.email,
        ip_address=get_client_ip(request),
    )

    await uow.commit()

    # TODO: Send reset email with token
    # For now, just return success (don't reveal if user exists)

    return MessageResponse(
        message="If an account with that email exists, a password reset link has been sent."
    )


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    data: PasswordResetConfirm,
    request: Request,
    uow: UnitOfWork = Depends(get_uow),
):
    """
    Reset password using token from email.

    This will invalidate all existing sessions.
    """
    auth = AuthService(uow)

    result = await auth.reset_password(
        token=data.token,
        new_password=data.new_password,
        ip_address=get_client_ip(request),
    )

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.error or "Password reset failed"
        )

    await uow.commit()

    return MessageResponse(message="Password reset successfully. Please login with your new password.")


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(
    data: EmailVerificationRequest,
    request: Request,
    uow: UnitOfWork = Depends(get_uow),
):
    """
    Verify email address using token from email.
    """
    auth = AuthService(uow)

    result = await auth.verify_email(
        token=data.token,
        ip_address=get_client_ip(request),
    )

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.error or "Email verification failed"
        )

    await uow.commit()

    return MessageResponse(message="Email verified successfully")


@router.post("/resend-verification", response_model=MessageResponse)
async def resend_verification_email(
    data: ResendVerificationRequest,
    uow: UnitOfWork = Depends(get_uow),
):
    """
    Resend email verification.

    For security, always returns success.
    """
    auth = AuthService(uow)

    success, token = await auth.resend_verification_email(data.email)

    await uow.commit()

    # TODO: Send verification email with token

    return MessageResponse(
        message="If an account with that email exists and is not verified, a verification email has been sent."
    )
