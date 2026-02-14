from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import CurrentUser, get_current_user
from app.schemas.auth import LoginRequest, MessageResponse, UserResponse, VerifyRequest
from app.services.auth import (
    create_jwt,
    create_magic_link_token,
    get_or_create_user,
    verify_magic_token,
)
from app.services.email import send_magic_link_email

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=MessageResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await get_or_create_user(db, request.email)
    raw_token = await create_magic_link_token(db, user)
    await send_magic_link_email(request.email, raw_token)
    return MessageResponse(message="Check your email for a login link.")


@router.post("/verify", response_model=UserResponse)
async def verify(
    request: VerifyRequest, response: Response, db: AsyncSession = Depends(get_db)
):
    user = await verify_magic_token(db, request.token)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    token = create_jwt(user.id, user.email, user.role.value)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        secure=True,
        max_age=7 * 24 * 60 * 60,
    )
    return UserResponse(
        id=user.id, email=user.email, role=user.role.value, created_at=user.created_at
    )


@router.post("/logout", response_model=MessageResponse)
async def logout(response: Response):
    response.delete_cookie("access_token")
    return MessageResponse(message="Logged out successfully.")


@router.get("/me", response_model=UserResponse)
async def me(current_user: CurrentUser = Depends(get_current_user)):
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        role=current_user.role.value,
        created_at=None,
    )
