import asyncio
import time
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import os
import logging

from app.config import config
from app.schemas import (
    VerificationRequest, VerificationResponse, HealthResponse, ReadinessResponse,
    ClaimResult, Verdict, ConfidenceBand
)
from app.providers import get_provider
from app.observability import RequestContext, get_metrics_summary, record_verdict, record_latency, metrics

logging.basicConfig(level=config.LOG_LEVEL)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI TruthGuard",
    description="Evidence-based AI claim verification system",
    version="0.1.0"
)

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
            message="Sample demo mode - ready to verify"
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


@app.post("/v1/verify", response_model=VerificationResponse)
async def verify(request: VerificationRequest):
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

        # Count verdicts
        supported = sum(1 for r in results if r.verdict == Verdict.SUPPORTED)
        refuted = sum(1 for r in results if r.verdict == Verdict.REFUTED)
        insufficient = sum(1 for r in results if r.verdict == Verdict.NOT_ENOUGH_EVIDENCE)
        abstain = sum(1 for r in results if r.verdict == Verdict.ABSTAIN)

        for result in results:
            record_verdict(result.verdict.value)

        latency_ms = (time.time() - start_time) * 1000
        record_latency(latency_ms)
        metrics["total_requests"] += 1
        metrics["total_claims_processed"] += len(claims)

        response = VerificationResponse(
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

        return response

    except Exception as e:
        metrics["model_failures"] += 1
        logger.error(f"[{ctx.request_id}] Verification failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics")
async def metrics_endpoint():
    return get_metrics_summary()


@app.get("/", response_class=FileResponse)
async def root():
    static_path = os.path.join(os.path.dirname(__file__), "static", "index.html")
    if os.path.exists(static_path):
        return static_path
    return {"message": "Frontend not yet built"}


# Serve static files
static_path = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_path):
    app.mount("/", StaticFiles(directory=static_path, html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=config.API_HOST,
        port=config.API_PORT,
        workers=config.API_WORKERS
    )
