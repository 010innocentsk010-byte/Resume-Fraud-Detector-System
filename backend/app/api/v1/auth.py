import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.core.security import create_access_token, create_refresh_token, decode_token, hash_password, verify_password
from app.core.security import InvalidTokenError
from app.db.session import get_db
from app.models.revoked_token import RevokedRefreshToken
from app.models.user import User
from app.schemas.user import RefreshRequest, TokenPair, UserCreate, UserRead

router = APIRouter(prefix="/auth", tags=["Authentication"])
logger = get_logger(__name__)


def _is_revoked(db: Session, jti: str | None) -> bool:
    if not jti:
        return False
    return db.scalar(select(RevokedRefreshToken).where(RevokedRefreshToken.jti == jti)) is not None


def _purge_expired_revocations(db: Session) -> None:
    db.query(RevokedRefreshToken).filter(RevokedRefreshToken.expires_at < datetime.now(timezone.utc)).delete()


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> User:
    existing = db.scalar(select(User).where(User.email == payload.email))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with this email already exists")

    user = User(
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=payload.role,
        organization=payload.organization,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info("New user registered: %s (role=%s)", user.email, user.role)
    return user


@router.post("/login", response_model=TokenPair)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)) -> TokenPair:
    user = db.scalar(select(User).where(User.email == form_data.username))
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated")

    return TokenPair(
        access_token=create_access_token(str(user.id), user.role.value),
        refresh_token=create_refresh_token(str(user.id)),
    )


@router.post("/refresh", response_model=TokenPair)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)) -> TokenPair:
    try:
        claims = decode_token(payload.refresh_token, expected_type="refresh")
    except InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token") from exc

    if _is_revoked(db, claims.get("jti")):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token has been revoked")

    user = db.get(User, uuid.UUID(claims["sub"]))
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    return TokenPair(
        access_token=create_access_token(str(user.id), user.role.value),
        refresh_token=create_refresh_token(str(user.id)),
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(payload: RefreshRequest, db: Session = Depends(get_db)) -> None:
    """Revokes the given refresh token so it can no longer mint new access
    tokens. Idempotent and never fails — an already-invalid or already-revoked
    token is simply a no-op, since the end state a caller wants (this token is
    dead) is already true.
    """
    _purge_expired_revocations(db)

    try:
        claims = decode_token(payload.refresh_token, expected_type="refresh")
    except InvalidTokenError:
        db.commit()
        return None

    jti = claims.get("jti")
    if jti and not _is_revoked(db, jti):
        expires_at = datetime.fromtimestamp(claims["exp"], tz=timezone.utc)
        db.add(RevokedRefreshToken(jti=jti, expires_at=expires_at))

    db.commit()
    return None
