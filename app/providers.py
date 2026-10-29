import httpx
import json
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from app.schemas import ClaimResult, Verdict, ConfidenceBand, EvidenceCitation
from app.config import config
import logging

logger = logging.getLogger(__name__)


class BaseProvider(ABC):
    @abstractmethod
    async def verify_claims(
        self, claims: List[str], evidence: List[Dict[str, Any]]
    ) -> List[ClaimResult]:
        pass

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        pass


class OllamaProvider(BaseProvider):
    def __init__(self, api_url: str = None, model: str = None):
        self.api_url = api_url or config.OLLAMA_API_URL
        self.model = model or config.OLLAMA_MODEL
        self.client = httpx.AsyncClient(timeout=config.REQUEST_TIMEOUT_SECONDS)

    @property
    def provider_name(self) -> str:
        return "ollama"

    @property
    def model_name(self) -> str:
        return self.model

    async def health_check(self) -> Dict[str, Any]:
        try:
            response = await self.client.get(f"{self.api_url}/api/tags")
            response.raise_for_status()
            models = response.json().get("models", [])
            model_names = [m["name"] for m in models]

            if self.model in model_names or any(self.model in m for m in model_names):
                return {
                    "status": "healthy",
                    "ollama_reachable": True,
                    "available_models": model_names,
                    "model": self.model
                }
            else:
                logger.warning(f"Model {self.model} not found in Ollama. Available: {model_names}")
                return {
                    "status": "healthy",
                    "ollama_reachable": True,
                    "available_models": model_names,
                    "model": self.model if self.model in model_names else None,
                    "warning": f"Model {self.model} not found"
                }
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return {
                "status": "unhealthy",
                "ollama_reachable": False,
                "error": str(e)
            }

    async def verify_claims(
        self, claims: List[str], evidence: List[Dict[str, Any]]
    ) -> List[ClaimResult]:
        results = []

        for claim_text in claims:
            try:
                evidence_text = "\n".join([
                    f"[{e.get('source_id', '?')}] {e.get('excerpt', '')}"
                    for e in evidence[:5]
                ])

                prompt = f"""You are a fact-checking system. Given a claim and evidence passages, classify the claim.

CLAIM: {claim_text}

EVIDENCE:
{evidence_text}

Respond with ONLY valid JSON (no markdown, no extra text):
{{
  "verdict": "SUPPORTED" or "REFUTED" or "NOT_ENOUGH_EVIDENCE" or "ABSTAIN",
  "confidence": "HIGH" or "MEDIUM" or "LOW",
  "explanation": "brief explanation",
  "cited_sources": ["source_id1", "source_id2"] or []
}}
"""

                response = await self.client.post(
                    f"{self.api_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "temperature": 0.1,
                    }
                )
                response.raise_for_status()
                response_data = response.json()

                try:
                    text_response = response_data.get("response", "").strip()
                    parsed = json.loads(text_response)

                    verdict = Verdict(parsed.get("verdict", "ABSTAIN"))
                    confidence = ConfidenceBand(parsed.get("confidence", "MEDIUM"))
                    explanation = parsed.get("explanation", "")
                    cited_sources = parsed.get("cited_sources", [])

                    cited_evidence = [
                        e for e in evidence
                        if e.get("source_id") in cited_sources
                    ]

                    result = ClaimResult(
                        claim_text=claim_text,
                        verdict=verdict,
                        confidence=confidence,
                        explanation=explanation,
                        evidence=[
                            EvidenceCitation(
                                source_id=e.get("source_id", "unknown"),
                                source_title=e.get("source_title", "Unknown"),
                                source_url=e.get("source_url"),
                                excerpt=e.get("excerpt", ""),
                                section=e.get("section"),
                                relevance_score=e.get("relevance_score"),
                            )
                            for e in cited_evidence
                        ],
                    )
                    results.append(result)
                except (json.JSONDecodeError, ValueError, KeyError) as parse_err:
                    logger.error(f"Failed to parse model response: {parse_err}")
                    result = ClaimResult(
                        claim_text=claim_text,
                        verdict=Verdict.ABSTAIN,
                        confidence=ConfidenceBand.LOW,
                        explanation="Model response validation failed",
                        evidence=[],
                        model_warning="Invalid model output format"
                    )
                    results.append(result)

            except Exception as e:
                logger.error(f"Error verifying claim: {e}")
                result = ClaimResult(
                    claim_text=claim_text,
                    verdict=Verdict.ABSTAIN,
                    confidence=ConfidenceBand.LOW,
                    explanation=f"Verification failed: {str(e)[:100]}",
                    evidence=[],
                    model_warning=f"Error: {type(e).__name__}"
                )
                results.append(result)

        return results


class FixtureProvider(BaseProvider):
    FIXTURE_DATA = {
        "supported_claim": {
            "claim_text": "DeepSeek-R1 is a 14 billion parameter model.",
            "verdict": Verdict.SUPPORTED,
            "confidence": ConfidenceBand.HIGH,
            "explanation": "The model is documented as DeepSeek-R1 with 14B parameters.",
            "evidence": [
                EvidenceCitation(
                    source_id="doc_001",
                    source_title="DeepSeek Model Card",
                    source_url="https://huggingface.co/deepseek-ai/deepseek-r1",
                    excerpt="DeepSeek-R1 is available in two sizes: 7B and 14B parameters.",
                    section="Model Specifications",
                    relevance_score=0.98
                )
            ]
        },
        "refuted_claim": {
            "claim_text": "DeepSeek-R1 is an open source model with unlimited usage.",
            "verdict": Verdict.REFUTED,
            "confidence": ConfidenceBand.MEDIUM,
            "explanation": "While DeepSeek is open source, usage is subject to its license terms.",
            "evidence": [
                EvidenceCitation(
                    source_id="doc_002",
                    source_title="DeepSeek License",
                    source_url="https://github.com/deepseek-ai/deepseek-r1",
                    excerpt="DeepSeek models are provided under the DeepSeek License, which includes restrictions on usage.",
                    section="License Terms",
                    relevance_score=0.95
                )
            ]
        },
        "insufficient_claim": {
            "claim_text": "DeepSeek-R1 is the most efficient model available.",
            "verdict": Verdict.NOT_ENOUGH_EVIDENCE,
            "confidence": ConfidenceBand.LOW,
            "explanation": "The corpus does not contain comparative efficiency benchmarks.",
            "evidence": []
        },
    }

    @property
    def provider_name(self) -> str:
        return "fixture"

    @property
    def model_name(self) -> str:
        return "deepseek-r1:14b (sample fixture)"

    async def health_check(self) -> Dict[str, Any]:
        return {
            "status": "healthy",
            "provider": "fixture",
            "message": "Sample demonstration mode - no live inference"
        }

    async def verify_claims(
        self, claims: List[str], evidence: List[Dict[str, Any]]
    ) -> List[ClaimResult]:
        results = []

        for claim in claims:
            lower_claim = claim.lower()

            if "14" in lower_claim and "parameter" in lower_claim:
                results.append(ClaimResult(**self.FIXTURE_DATA["supported_claim"]))
            elif "unlimited" in lower_claim or "unrestricted" in lower_claim:
                results.append(ClaimResult(**self.FIXTURE_DATA["refuted_claim"]))
            elif "efficient" in lower_claim or "efficiency" in lower_claim:
                results.append(ClaimResult(**self.FIXTURE_DATA["insufficient_claim"]))
            else:
                results.append(ClaimResult(
                    claim_text=claim,
                    verdict=Verdict.ABSTAIN,
                    confidence=ConfidenceBand.LOW,
                    explanation="Claim does not match fixture examples",
                    evidence=[]
                ))

        return results


def get_provider() -> BaseProvider:
    if config.PROVIDER_MODE == "local":
        return OllamaProvider()
    else:
        return FixtureProvider()
