from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class Verdict(str, Enum):
    SUPPORTED = "SUPPORTED"
    REFUTED = "REFUTED"
    NOT_ENOUGH_EVIDENCE = "NOT_ENOUGH_EVIDENCE"
    ABSTAIN = "ABSTAIN"


class ConfidenceBand(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class EvidenceCitation(BaseModel):
    source_id: str
    source_title: str
    source_url: Optional[str] = None
    excerpt: str
    section: Optional[str] = None
    relevance_score: Optional[float] = None


class NumericCheck(BaseModel):
    baseline_value: float
    current_value: float
    difference: float
    is_consistent: bool
    explanation: Optional[str] = None


class ClaimResult(BaseModel):
    claim_text: str
    verdict: Verdict
    confidence: ConfidenceBand
    explanation: str
    evidence: List[EvidenceCitation] = []
    numeric_check: Optional[NumericCheck] = None
    model_warning: Optional[str] = None


class VerificationRequest(BaseModel):
    text: str = Field(..., max_length=5000, description="Text to verify")
    mode: Optional[str] = Field("auto", description="auto, local, or fixture")
    top_k: Optional[int] = Field(5, description="Number of evidence passages to retrieve")


class VerificationResponse(BaseModel):
    request_id: str
    provider: str
    model: str
    prompt_version: str
    corpus_version: str
    latency_ms: float
    claims: List[ClaimResult]
    total_claims: int
    supported_count: int
    refuted_count: int
    insufficient_evidence_count: int
    abstain_count: int


class HealthResponse(BaseModel):
    status: str
    provider: str
    model: Optional[str] = None
    ollama_reachable: Optional[bool] = None
    timestamp: str


class ReadinessResponse(BaseModel):
    ready: bool
    provider: str
    model: Optional[str] = None
    corpus_loaded: bool
    message: str


class SignUpRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    password: str = Field(..., min_length=8)


class SignInRequest(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    created_at: str


class VerificationHistoryItem(BaseModel):
    id: int
    request_id: str
    text_preview: str
    total_claims: int
    supported_count: int
    refuted_count: int
    insufficient_evidence_count: int
    abstain_count: int
    provider: str
    model: str
    latency_ms: float
    created_at: str


class DashboardResponse(BaseModel):
    user: UserResponse
    total_verifications: int
    total_claims_processed: int
    average_latency_ms: float
    recent_history: List[VerificationHistoryItem]
