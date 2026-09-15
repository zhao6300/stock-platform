from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Literal

from stock_platform.domain.common import JsonObject, canonical_json

type AIAnalysisIntent = Literal["OVERVIEW", "RANGE", "CENTRAL_TENDENCY", "VOLATILITY"]
type AIConfidence = Literal["EVIDENCE_BACKED", "INSUFFICIENT_EVIDENCE"]
type AIMetricKind = Literal["COUNT", "MIN", "MEAN", "MEDIAN", "MAX", "VARIANCE", "RANGE"]

AI_INTENT_VALUES = ("OVERVIEW", "RANGE", "CENTRAL_TENDENCY", "VOLATILITY")


@dataclass(frozen=True, slots=True)
class AIEvidence:
    """A bounded and content-addressed link between text and platform data."""

    evidence_id: str
    entity: str
    snapshot_id: str
    filters: tuple[tuple[str, str], ...]
    row_count: int
    result_sha256: str


@dataclass(frozen=True, slots=True)
class AIMetric:
    """One canonical metric owned by the deterministic reasoning rule set."""

    metric_id: str
    kind: AIMetricKind
    field: str | None
    value: str | None


@dataclass(frozen=True, slots=True)
class AIFinding:
    """A single statement backed by explicit local evidence."""

    finding_id: str
    statement: str
    confidence: AIConfidence
    evidence_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AIAnalysisArtifact:
    """An immutable provenance-bearing output of one AI analysis."""

    analysis_id: str
    snapshot_id: str
    entity: str
    filters: tuple[tuple[str, str], ...]
    intent: AIAnalysisIntent
    metric_field: str | None
    provider_id: str
    model_id: str
    model_version: str
    prompt_template_version: str
    reasoning_rule_set_version: str
    row_count: int
    summary: str
    findings: tuple[AIFinding, ...]
    metrics: tuple[AIMetric, ...]
    evidence: tuple[AIEvidence, ...]
    limitations: tuple[str, ...]

    def as_dict(self) -> JsonObject:
        """Return the canonical, schema-safe representation used by identifiers."""
        return {
            "analysis_id": self.analysis_id,
            "snapshot_id": self.snapshot_id,
            "entity": self.entity,
            "filters": [{"field": key, "value": value} for key, value in self.filters],
            "intent": self.intent,
            "metric_field": self.metric_field,
            "provider_id": self.provider_id,
            "model_id": self.model_id,
            "model_version": self.model_version,
            "prompt_template_version": self.prompt_template_version,
            "reasoning_rule_set_version": self.reasoning_rule_set_version,
            "row_count": self.row_count,
            "summary": self.summary,
            "findings": [
                {
                    "finding_id": finding.finding_id,
                    "statement": finding.statement,
                    "confidence": finding.confidence,
                    "evidence_ids": list(finding.evidence_ids),
                }
                for finding in self.findings
            ],
            "metrics": [
                {
                    "metric_id": metric.metric_id,
                    "kind": metric.kind,
                    "field": metric.field,
                    "value": metric.value,
                }
                for metric in self.metrics
            ],
            "evidence": [
                {
                    "evidence_id": evidence.evidence_id,
                    "entity": evidence.entity,
                    "snapshot_id": evidence.snapshot_id,
                    "filters": [
                        {"field": key, "value": value} for key, value in evidence.filters
                    ],
                    "row_count": evidence.row_count,
                    "result_sha256": evidence.result_sha256,
                }
                for evidence in self.evidence
            ],
            "limitations": list(self.limitations),
        }


def analysis_identifier(artifact: AIAnalysisArtifact) -> str:
    """Create the content-bound identifier for one complete AI artifact."""
    contents = artifact.as_dict()
    contents.pop("analysis_id")
    digest = sha256(canonical_json(contents).encode("utf-8")).hexdigest()
    return f"ai-sha256:{digest}"


def parse_ai_analysis_intent(value: str) -> AIAnalysisIntent | None:
    """Reject an unknown intent before composing an application request."""
    normalized = value.strip().upper()
    if normalized == "OVERVIEW":
        return "OVERVIEW"
    if normalized == "RANGE":
        return "RANGE"
    if normalized == "CENTRAL_TENDENCY":
        return "CENTRAL_TENDENCY"
    if normalized == "VOLATILITY":
        return "VOLATILITY"
    return None


def ai_finding_id(number: int) -> str:
    """Create the stable finding identifier for one local analysis."""
    return f"finding-{number:03d}"


def ai_evidence_id(number: int) -> str:
    """Create the stable evidence identifier for one local analysis."""
    return f"evidence-{number:03d}"
