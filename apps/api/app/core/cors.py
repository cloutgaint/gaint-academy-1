from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

def configure_cors(app):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET","POST","PUT","PATCH","DELETE","OPTIONS"],
        allow_headers=["Content-Type","X-Request-ID","Idempotency-Key","X-CSRF-Token"],
    )
