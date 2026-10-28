from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from .config import ACCESS_TOKEN_MINUTES, SECRET_KEY

ALGO = "HS256"


def hash_password(pw: str) -> str:
    return bcrypt.hashpw(pw.encode()[:72], bcrypt.gensalt()).decode()


def verify_password(pw: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(pw.encode()[:72], hashed.encode())
    except ValueError:
        return False


def create_token(user_id: int) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_MINUTES)
    return jwt.encode({"sub": str(user_id), "exp": exp}, SECRET_KEY, algorithm=ALGO)


def decode_token(token: str) -> int | None:
    try:
        return int(jwt.decode(token, SECRET_KEY, algorithms=[ALGO])["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        return None
