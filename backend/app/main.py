from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.core.limiter import limiter
from slowapi.errors import RateLimitExceeded
from slowapi._rate_limit_exceeded_handler import _rate_limit_exceeded_handler

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/")
@limiter.limit("10/minute")
def read_root(request: Request):
    return {"app_name": "Financial Research Agent", "version": "1.0.0", "status": "running"}

@app.get("/health")
@limiter.limit("10/minute")
def health_check(request: Request):
    return {"status": "ok"}