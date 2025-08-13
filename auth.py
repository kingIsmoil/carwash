from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from uuid import uuid4

from database import AsyncSessionLocal
from models import User, UserRole   
from auth_model import RefreshToken
from schemas import UserCreate, UserOut, Token,LoginRequest
from security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, decode_token,REFRESH_TOKEN_EXPIRE_DAYS
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/auth", tags=["auth"])

# --- Dependency: DB session ---
def get_db():
    db = AsyncSessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- Register ---
@router.post("/register", response_model=UserOut, status_code=201)
async def register(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    # email уникален
    result = await db.execute(select(User).where(User.email == payload.email))
    existing_user = result.scalars().first()
    if existing_user:
        raise HTTPException(status_code=409, detail="Email already in use")

    # phone_number уникален
    result = await db.execute(select(User).where(User.phone_number == payload.phone_number))
    existing_phone = result.scalars().first()
    if existing_phone:
        raise HTTPException(status_code=409, detail="Phone already in use")

    # создаём пользователя
    user = User(
        fullname=payload.fullname,
        email=payload.email,
        phone_number=payload.phone_number,
        password_hash=hash_password(payload.password),
        role=UserRole.user,  # по умолчанию
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/login", response_model=Token)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    # Ищем пользователя по email
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Генерация токенов
    refresh_jti = str(uuid4())
    access_token = create_access_token(sub=str(user.id), role=user.role.value)
    refresh_token = create_refresh_token(sub=str(user.id), jti=refresh_jti)

    # Сохраняем refresh-токен в БД
    expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    db.add(RefreshToken(user_id=user.id, jti=refresh_jti, expires_at=expires_at))
    await db.commit()

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )


# --- Refresh ---
from datetime import timedelta
@router.post("/refresh", response_model=Token)
def refresh_token(request: Request, db: Session = Depends(get_db)):
    # ожидаем refresh token в Authorization: Bearer <token>
    auth = request.headers.get("Authorization")
    if not auth or not auth.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing refresh token")
    token = auth.split(" ", 1)[1]

    try:
        payload = decode_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Not a refresh token")

    user_id = int(payload["sub"])
    jti = payload["jti"]

    rec = db.query(RefreshToken).filter(RefreshToken.jti == jti).first()
    if not rec or rec.revoked:
        raise HTTPException(status_code=401, detail="Refresh token revoked")
    if rec.expires_at <= datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Refresh token expired")

    user = db.query(User).get(user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=403, detail="User disabled")

    # Ротация refresh: текущий ревокируем, выдаём новый
    rec.revoked = True
    new_refresh_jti = str(uuid4())
    new_access = create_access_token(sub=str(user.id), role=user.role.value)
    new_refresh = create_refresh_token(sub=str(user.id), jti=new_refresh_jti)

    from security import REFRESH_TOKEN_EXPIRE_DAYS
    expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    db.add(RefreshToken(user_id=user.id, jti=new_refresh_jti, expires_at=expires_at))
    db.commit()

    return Token(access_token=new_access, refresh_token=new_refresh)

# --- Logout ---
@router.post("/logout")
def logout(request: Request, db: Session = Depends(get_db)):
    # Принимаем refresh token и ревокируем его
    auth = request.headers.get("Authorization")
    if not auth or not auth.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing refresh token")
    token = auth.split(" ", 1)[1]

    try:
        payload = decode_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Not a refresh token")

    jti = payload["jti"]
    rec = db.query(RefreshToken).filter(RefreshToken.jti == jti).first()
    if not rec:
        # идемпотентность логаута
        return {"detail": "Logged out"}

    rec.revoked = True
    db.commit()
    return {"detail": "Logged out"}
