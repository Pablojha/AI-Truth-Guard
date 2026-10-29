import time
from datetime import datetime, timedelta
import io
from fastapi import FastAPI, HTTPException, Depends, Response, Cookie, Header, UploadFile, File
from pypdf import PdfReader
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os
import logging
import json
from typing import List, Optional

from app.config import config
from app.schemas import (
    VerificationRequest, VerificationResponse, HealthResponse, ReadinessResponse,
    ClaimResult, Verdict, ConfidenceBand, SignUpRequest, SignInRequest,
    UserResponse, DashboardResponse, VerificationHistoryItem,
    PaymentSubmitRequest, PaymentRequestItem
)
from app.providers import get_provider
from app.observability import RequestContext, get_metrics_summary, record_verdict, record_latency, metrics
from app.database import init_db, get_db, User, VerificationHistory, PaymentRequest
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

    if config.PROVIDER_MODE == "websearch":
        # Evidence-based provider is always ready (no external dependencies)
        return ReadinessResponse(
            ready=True,
            provider=provider.provider_name,
            model=provider.model_name,
            corpus_loaded=True,
            message="Evidence-based verification ready"
        )

    # Local Ollama provider
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

    if not current_user:
        raise HTTPException(status_code=401, detail=f"Sign up to get {FREE_CHECKS} free checks")
    if not _active_subscription(db, current_user.id):
        if _free_checks_used(db, current_user.id) >= FREE_CHECKS:
            raise HTTPException(
                status_code=402,
                detail=f"You have used your {FREE_CHECKS} free checks. Choose a plan to continue."
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


PLAN_PRICING = {
    "weekly": {"amount_inr": 699, "days": 7},
    "monthly": {"amount_inr": 2200, "days": 30},
    "yearly": {"amount_inr": 11999, "days": 365},
}

FREE_CHECKS = 5


def _active_subscription(db: Session, user_id: int) -> Optional[PaymentRequest]:
    return (
        db.query(PaymentRequest)
        .filter(
            PaymentRequest.user_id == user_id,
            PaymentRequest.status == "approved",
            PaymentRequest.expires_at > datetime.utcnow(),
        )
        .order_by(PaymentRequest.expires_at.desc())
        .first()
    )


def _free_checks_used(db: Session, user_id: int) -> int:
    return db.query(VerificationHistory).filter(VerificationHistory.user_id == user_id).count()


def _payment_item(p: PaymentRequest) -> PaymentRequestItem:
    return PaymentRequestItem(
        id=p.id,
        user_id=p.user_id,
        plan=p.plan,
        amount_inr=p.amount_inr,
        utr=p.utr,
        status=p.status,
        created_at=p.created_at.isoformat(),
        expires_at=p.expires_at.isoformat() if p.expires_at else None,
    )


def _require_admin(x_admin_token: Optional[str]):
    if not config.ADMIN_TOKEN or x_admin_token != config.ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Admin access denied")


@app.get("/api/payments/config")
async def payment_config():
    return {
        "upi_id": config.UPI_ID,
        "payee_name": config.UPI_PAYEE_NAME,
        "plans": {k: v["amount_inr"] for k, v in PLAN_PRICING.items()},
    }


@app.post("/api/payments/submit", response_model=PaymentRequestItem)
async def submit_payment(
    request: PaymentSubmitRequest,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Sign in before paying")
    if not config.UPI_ID:
        raise HTTPException(status_code=503, detail="Payments are not configured")

    utr = request.utr.upper()
    if db.query(PaymentRequest).filter(PaymentRequest.utr == utr).first():
        raise HTTPException(status_code=400, detail="This transaction reference was already submitted")

    payment = PaymentRequest(
        user_id=current_user.id,
        plan=request.plan,
        amount_inr=PLAN_PRICING[request.plan]["amount_inr"],
        utr=utr,
        status="pending",
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return _payment_item(payment)


@app.get("/api/payments/status")
async def payment_status(
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    active = _active_subscription(db, current_user.id)
    return {
        "active": active is not None,
        "plan": active.plan if active else None,
        "expires_at": active.expires_at.isoformat() if active else None,
        "free_checks_left": None if active else max(0, FREE_CHECKS - _free_checks_used(db, current_user.id)),
    }


@app.get("/api/admin/payments", response_model=List[PaymentRequestItem])
async def list_payments(
    status: str = "pending",
    x_admin_token: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    _require_admin(x_admin_token)
    rows = db.query(PaymentRequest).filter(PaymentRequest.status == status).order_by(PaymentRequest.created_at).all()
    return [_payment_item(p) for p in rows]


@app.post("/api/admin/payments/{payment_id}/{decision}", response_model=PaymentRequestItem)
async def review_payment(
    payment_id: int,
    decision: str,
    x_admin_token: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    _require_admin(x_admin_token)
    if decision not in ("approve", "reject"):
        raise HTTPException(status_code=404, detail="Unknown decision")
    payment = db.query(PaymentRequest).filter(PaymentRequest.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    if payment.status != "pending":
        raise HTTPException(status_code=400, detail=f"Payment already {payment.status}")

    now = datetime.utcnow()
    payment.reviewed_at = now
    if decision == "approve":
        payment.status = "approved"
        payment.expires_at = now + timedelta(days=PLAN_PRICING[payment.plan]["days"])
    else:
        payment.status = "rejected"
    db.commit()
    db.refresh(payment)
    return _payment_item(payment)


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

@app.post("/api/extract-pdf")
async def extract_pdf(
    file: UploadFile = File(...),
    current_user: Optional[User] = Depends(get_current_user),
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Sign in to upload files")
    if file.content_type != "application/pdf" and not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files can be read here")

    data = await file.read(10 * 1024 * 1024 + 1)
    if len(data) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large (max 10MB)")

    try:
        reader = PdfReader(io.BytesIO(data))
        text = "\n".join((page.extract_text() or "").strip() for page in reader.pages).strip()
    except Exception:
        raise HTTPException(status_code=400, detail="Could not read this PDF")

    if not text:
        raise HTTPException(status_code=400, detail="No selectable text found in this PDF (scanned PDFs are not supported)")
    return {"text": text[: config.MAX_INPUT_LENGTH], "truncated": len(text) > config.MAX_INPUT_LENGTH}


@app.get("/admin", include_in_schema=False)
async def serve_admin():
    admin_path = os.path.join(os.path.dirname(__file__), "static", "admin.html")
    if os.path.exists(admin_path):
        return FileResponse(admin_path, media_type="text/html")
    raise HTTPException(status_code=404, detail="admin.html not found")

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
