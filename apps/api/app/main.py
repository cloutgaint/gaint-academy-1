from fastapi import FastAPI, HTTPException
from sqlalchemy import text
from app.core.config import settings
from app.core.request_id import RequestIdMiddleware
from app.core.csrf import CSRFMiddleware
from app.core.cors import configure_cors
from app.api.v1.router import router as v1_router
from app.db.session import engine
app=FastAPI(title=settings.app_name,version="0.1.0")
configure_cors(app)
app.add_middleware(RequestIdMiddleware)
app.add_middleware(CSRFMiddleware)
app.include_router(v1_router)
@app.get("/health/live",tags=["health"])
def live(): return {"status":"ok","service":"api"}
@app.get("/health/ready",tags=["health"])
def ready():
    try:
        with engine.connect() as c: c.execute(text("SELECT 1"))
        return {"status":"ready","service":"api","database":"ok"}
    except Exception as exc:
        raise HTTPException(status_code=503,detail="Database not ready") from exc
