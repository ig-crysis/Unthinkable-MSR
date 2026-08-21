import secrets

from fastapi import Request, Response

from app.core.config import settings

OWNER_COOKIE_NAME = "moid"
OWNER_COOKIE_MAX_AGE = 60 * 60 * 24 * 365  # 1 year


def get_owner_id(request: Request, response: Response) -> str:
    """Identifies which browser/visitor a meeting belongs to.

    There's no login for this project (single-user by design), but the app
    is now hosted where anyone can reach it, so meetings need to stay
    private per-visitor. A random id in an httpOnly cookie does that without
    requiring accounts: each new visitor is silently issued their own id on
    first request and only ever sees meetings tagged with it.
    """
    owner_id = request.cookies.get(OWNER_COOKIE_NAME)
    if not owner_id:
        owner_id = secrets.token_urlsafe(24)
        response.set_cookie(
            key=OWNER_COOKIE_NAME,
            value=owner_id,
            max_age=OWNER_COOKIE_MAX_AGE,
            httponly=True,
            samesite="lax",
            secure=settings.cookie_secure,
        )
    return owner_id
