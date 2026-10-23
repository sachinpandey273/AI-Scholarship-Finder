from dataclasses import dataclass
from uuid import UUID, NAMESPACE_URL, uuid5
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from .config import Settings, get_settings

bearer = HTTPBearer(auto_error=False)

@dataclass(frozen=True)
class Principal:
    user_id: UUID
    subject: str

def current_principal(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    settings: Settings = Depends(get_settings),
) -> Principal:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    try:
        claims = jwt.decode(
            credentials.credentials, settings.jwt_public_key,
            algorithms=["RS256"], issuer=settings.jwt_issuer,
            audience=settings.jwt_audience,
            options={"require": ["exp", "sub"]},
        )
        subject = str(claims["sub"])
        # OIDC subjects are opaque strings (and are not necessarily UUIDs).
        # A stable UUID keeps the relational ownership key compact while the
        # original opaque subject is retained uniquely in the users table.
        return Principal(user_id=uuid5(NAMESPACE_URL, f"{settings.jwt_issuer}:{subject}"), subject=subject)
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail="Invalid access token") from exc
