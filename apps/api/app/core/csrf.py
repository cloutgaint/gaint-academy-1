import secrets
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from app.core.auth import SESSION_COOKIE

CSRF_COOKIE="gaint_csrf"
CSRF_HEADER="x-csrf-token"
SAFE_METHODS={"GET","HEAD","OPTIONS"}

def new_csrf_token()->str:
    return secrets.token_urlsafe(32)

class CSRFMiddleware(BaseHTTPMiddleware):
    async def dispatch(self,request:Request,call_next):
        if request.method.upper() not in SAFE_METHODS and request.cookies.get(SESSION_COOKIE):
            cookie=request.cookies.get(CSRF_COOKIE)
            header=request.headers.get(CSRF_HEADER)
            if not cookie or not header or not secrets.compare_digest(cookie,header):
                return JSONResponse(status_code=403,content={"detail":"CSRF validation failed"})
        return await call_next(request)
