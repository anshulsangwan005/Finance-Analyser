from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from .database import get_db
from .models import User
from .security import decode_token

bearer = HTTPBearer(auto_error=False)


def get_current_user(cred: HTTPAuthorizationCredentials = Depends(bearer), db: Session = Depends(get_db)) -> User:
    uid = decode_token(cred.credentials) if cred else None
    user = db.get(User, uid) if uid else None
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user
