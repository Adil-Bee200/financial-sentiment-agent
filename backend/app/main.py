from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.router import router as api_router
from app.core.config import settings
from app.core.database import get_db
from app.core.limiter import limiter

app = FastAPI(
    title=settings.APP_NAME,
    description="Read-only API for financial sentiment data",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(api_router)


@app.get("/")
@limiter.limit("60/minute")
def read_root(request: Request):
    return {"app_name": settings.APP_NAME, "version": "1.0.0", "status": "running"}


@app.get("/health")
@limiter.limit("60/minute")
def health_check(request: Request, db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "connected"}
