from __future__ import annotations

from stock_platform.domain.ai import (
    AIAnalysisArtifact,
    AIEvidence,
    AIFinding,
    AIMetric,
)
from stock_platform.domain.common import canonical_json


def artifact() -> AIAnalysisArtifact:
    """Return a minimal fixture with the same key structure as production."""
    return AIAnalysisArtifact(
        analysis_id="ai-sha256:test",
        snapshot_id="sha256:123",
        entity="security_master",
        filters=(("market", "NASDAQ"),),
        intent="OVERVIEW",
        metric_field=None,
        provider_id="local-evidence-reasoner",
        model_id="platform-evidence-reasoner",
        model_version="test",
        prompt_template_version="test-prompt",
        reasoning_rule_set_version="test-rules",
        row_count=1,
        summary="one row",
        findings=(
            AIFinding("finding-001", "one row is present", "EVIDENCE_BACKED", ("evidence-001",)),
        ),
        metrics=(AIMetric("metric-001", "COUNT", None, "1"),),
        evidence=(
            AIEvidence(
                evidence_id="evidence-001",
                entity="security_master",
                snapshot_id="sha256:123",
                filters=(("market", "NASDAQ"),),
                row_count=1,
                result_sha256="0" * 64,
            ),
        ),
        limitations=("test limitation",),
    )


def test_ai_artifact_serializes_to_schema_safe_json() -> None:
    encoded = canonical_json(artifact().as_dict())

    assert "ai-sha256:test" in encoded
    assert '"confidence":"EVIDENCE_BACKED"' in encoded


def test_ai_artifact_identifier_is_content_bound() -> None:
    from stock_platform.domain.ai import analysis_identifier

    first = artifact()
    second = artifact()
    different = artifact()
    object.__setattr__(different, "summary", "changed")

    assert analysis_identifier(first) == analysis_identifier(second)
    assert analysis_identifier(first) != analysis_identifier(different)
