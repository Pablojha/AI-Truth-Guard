import time
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Depends, Response, Cookie
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os
import logging
import json
from typing import Optional

from app.config import config
from app.schemas import (
    VerificationRequest, VerificationResponse, HealthResponse, ReadinessResponse,
    ClaimResult, Verdict, ConfidenceBand, SignUpRequest, SignInRequest,
    UserResponse, DashboardResponse, VerificationHistoryItem
)
from app.providers import get_provider
from app.observability import RequestContext, get_metrics_summary, record_verdict, record_latency, metrics
from app.database import init_db, get_db, User, VerificationHistory
from app.auth import (
    create_user, authenticate_user, get_user_by_username,
    get_user_by_email, get_user_by_id, hash_password
)

logging.basicConfig(level=config.LOG_LEVEL)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI TruthGuard",
    description="Evidence-based AI claim verification system",
    version="0.1.0"
)

# Initialize database
init_db()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Provider
provider = get_provider()


def get_current_user(user_id: Optional[int] = Cookie(None), db: Session = Depends(get_db)) -> Optional[User]:
    if user_id is None:
        return None
    return get_user_by_id(db, user_id)


# ============================================================================
# HEALTH AND STATUS ENDPOINTS
# ============================================================================

@app.get("/healthz", response_model=HealthResponse)
async def health():
    health_check = await provider.health_check()
    return HealthResponse(
        status="healthy" if config.PROVIDER_MODE == "fixture" else health_check.get("status", "unknown"),
        provider=provider.provider_name,
        model=provider.model_name,
        ollama_reachable=health_check.get("ollama_reachable") if config.PROVIDER_MODE == "local" else None,
        timestamp=datetime.utcnow().isoformat()
    )


@app.get("/readyz", response_model=ReadinessResponse)
async def readiness():
    if config.PROVIDER_MODE == "fixture":
        return ReadinessResponse(
            ready=True,
            provider="fixture",
            model=provider.model_name,
            corpus_loaded=True,
            message="Demo mode active - precomputed sample results only"
        )

    health_check = await provider.health_check()
    is_healthy = health_check.get("ollama_reachable", False)

    return ReadinessResponse(
        ready=is_healthy,
        provider=provider.provider_name,
        model=provider.model_name if is_healthy else None,
        corpus_loaded=is_healthy,
        message="Ready" if is_healthy else "Ollama not reachable"
    )


# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@app.post("/api/auth/signup")
async def signup(request: SignUpRequest, db: Session = Depends(get_db)):
    if get_user_by_username(db, request.username):
        raise HTTPException(status_code=400, detail="Username already exists")
    if get_user_by_email(db, request.email):
        raise HTTPException(status_code=400, detail="Email already exists")

    user = create_user(db, request.username, request.email, request.password)

    return {
        "message": "User created successfully",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email
        }
    }


@app.post("/api/auth/signin")
async def signin(request: SignInRequest, response: Response, db: Session = Depends(get_db)):
    user = authenticate_user(db, request.username, request.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    response.set_cookie(
        key="user_id",
        value=str(user.id),
        max_age=7 * 24 * 60 * 60,
        secure=False,
        httponly=True,
        samesite="lax"
    )

    return {
        "message": "Signed in successfully",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email
        }
    }


@app.post("/api/auth/signout")
async def signout(response: Response):
    response.delete_cookie(key="user_id")
    return {"message": "Signed out successfully"}


@app.get("/api/auth/me", response_model=UserResponse)
async def get_me(current_user: Optional[User] = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        created_at=current_user.created_at.isoformat()
    )


# ============================================================================
# VERIFICATION ENDPOINT (Optional Auth)
# ============================================================================

@app.post("/v1/verify", response_model=VerificationResponse)
async def verify(
    request: VerificationRequest,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if len(request.text) > config.MAX_INPUT_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"Input exceeds maximum length of {config.MAX_INPUT_LENGTH}"
        )

    ctx = RequestContext()
    start_time = time.time()

    try:
        ctx.add_event("verify_start", {"input_length": len(request.text)})

        # Extract claims (simple sentence splitting for now)
        sentences = [s.strip() for s in request.text.split(".") if s.strip()]
        claims = sentences[:config.MAX_CLAIMS_PER_REQUEST]

        if not claims:
            raise ValueError("No claims could be extracted from input")

        ctx.add_event("claims_extracted", {"count": len(claims)})

        # For now, use empty evidence retrieval (will be implemented in Milestone 2)
        evidence = []

        # Verify claims
        results = await provider.verify_claims(claims, evidence)

        ctx.add_event("verification_complete", {"results_count": len(results)})

        # Count verdicts (support both old and new verdict names)
        supported = sum(1 for r in results if r.verdict in (Verdict.SUPPORTED, Verdict.VERIFIED_TRUE))
        refuted = sum(1 for r in results if r.verdict in (Verdict.REFUTED, Verdict.VERIFIED_FALSE))
        insufficient = sum(1 for r in results if r.verdict in (Verdict.NOT_ENOUGH_EVIDENCE, Verdict.INSUFFICIENT_EVIDENCE))
        abstain = sum(1 for r in results if r.verdict == Verdict.ABSTAIN)

        for result in results:
            record_verdict(result.verdict.value)

        latency_ms = (time.time() - start_time) * 1000
        record_latency(latency_ms)
        metrics["total_requests"] += 1
        metrics["total_claims_processed"] += len(claims)

        response_obj = VerificationResponse(
            request_id=ctx.request_id,
            provider=provider.provider_name,
            model=provider.model_name,
            prompt_version=config.PROMPT_VERSION,
            corpus_version=config.CORPUS_VERSION,
            latency_ms=latency_ms,
            claims=results,
            total_claims=len(results),
            supported_count=supported,
            refuted_count=refuted,
            insufficient_evidence_count=insufficient,
            abstain_count=abstain
        )

        logger.info(f"[{ctx.request_id}] Verification complete: {supported} supported, {refuted} refuted, {insufficient} insufficient")

        # Save to history if user is authenticated
        if current_user:
            text_preview = request.text[:250] if len(request.text) <= 250 else request.text[:247] + "..."
            history = VerificationHistory(
                user_id=current_user.id,
                request_id=ctx.request_id,
                text=request.text,
                text_preview=text_preview,
                total_claims=len(results),
                supported_count=supported,
                refuted_count=refuted,
                insufficient_evidence_count=insufficient,
                abstain_count=abstain,
                provider=provider.provider_name,
                model=provider.model_name,
                latency_ms=latency_ms
            )
            db.add(history)
            db.commit()

        return response_obj

    except Exception as e:
        metrics["model_failures"] += 1
        logger.error(f"[{ctx.request_id}] Verification failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# DASHBOARD ENDPOINT (Protected)
# ============================================================================

@app.get("/api/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Get user's verification history
    history = db.query(VerificationHistory).filter(
        VerificationHistory.user_id == current_user.id
    ).order_by(VerificationHistory.created_at.desc()).limit(10).all()

    # Calculate stats
    total_verifications = db.query(VerificationHistory).filter(
        VerificationHistory.user_id == current_user.id
    ).count()

    total_claims = sum(h.total_claims for h in history) if history else 0
    avg_latency = sum(h.latency_ms for h in history) / len(history) if history else 0.0

    # Format history
    history_items = [
        VerificationHistoryItem(
            id=h.id,
            request_id=h.request_id,
            text_preview=h.text_preview,
            total_claims=h.total_claims,
            supported_count=h.supported_count,
            refuted_count=h.refuted_count,
            insufficient_evidence_count=h.insufficient_evidence_count,
            abstain_count=h.abstain_count,
            provider=h.provider,
            model=h.model,
            latency_ms=h.latency_ms,
            created_at=h.created_at.isoformat()
        )
        for h in history
    ]

    return DashboardResponse(
        user=UserResponse(
            id=current_user.id,
            username=current_user.username,
            email=current_user.email,
            created_at=current_user.created_at.isoformat()
        ),
        total_verifications=total_verifications,
        total_claims_processed=total_claims,
        average_latency_ms=avg_latency,
        recent_history=history_items
    )


@app.get("/metrics")
async def metrics_endpoint():
    return get_metrics_summary()


# ============================================================================
# STATIC FILES
# ============================================================================

@app.get("/", include_in_schema=False)
async def serve_index():
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path, media_type="text/html")
    raise HTTPException(status_code=404, detail="index.html not found")

static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=config.API_HOST,
        port=config.API_PORT,
        workers=config.API_WORKERS
    )
