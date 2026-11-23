from datetime import datetime, timedelta
import bcrypt
from fastapi import Depends, HTTPException
from sqlmodel import Session, select
from app.database import get_session
from app.models import User
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

from app.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_HOURS

security = HTTPBearer()
optional_security = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def create_token(data: dict) -> str:
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    return jwt.encode({**data, "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="无效的令牌")


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: Session = Depends(get_session),
) -> dict:
    payload = decode_token(credentials.credentials)
    if payload.get("type") == "github" or payload.get("admin") is not True:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    user = session.exec(select(User).where(User.username == payload.get("sub"))).first()
    if not user or not user.is_admin:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return payload


def get_optional_admin(
    credentials: HTTPAuthorizationCredentials | None = Depends(optional_security),
    session: Session = Depends(get_session),
) -> dict | None:
    if credentials is None:
        return None
    try:
        return get_current_user(credentials, session)
    except HTTPException as exc:
        if exc.status_code in (401, 403):
            return None
        raise
