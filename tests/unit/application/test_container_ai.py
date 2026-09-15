from __future__ import annotations

from stock_platform.application.container import ApplicationContainer


def test_container_registers_content_addressed_ai_artifacts() -> None:
    from stock_platform.domain.ai import (
        AIAnalysisArtifact,
        AIEvidence,
        AIFinding,
        AIMetric,
    )

    container = ApplicationContainer()
    artifact = AIAnalysisArtifact(
        analysis_id="ai-sha256:test",
        snapshot_id="sha256:123",
        entity="security_master",
        filters=(),
        intent="OVERVIEW",
        metric_field=None,
        provider_id="local-evidence-reasoner",
        model_id="platform-evidence-reasoner",
        model_version="test",
        prompt_template_version="test-prompt",
        reasoning_rule_set_version="test-rules",
        row_count=1,
        summary="one row",
        findings=(AIFinding("finding-001", "one row", "EVIDENCE_BACKED", ("evidence-001",)),),
        metrics=(AIMetric("metric-001", "COUNT", None, "1"),),
        evidence=(
            AIEvidence("evidence-001", "security_master", "sha256:123", (), 1, "0" * 64),
        ),
        limitations=("test",),
    )

    analysis_id = container.record_ai_analysis(artifact)
    state = container.backup_platform_state()

    assert analysis_id == artifact.analysis_id
    assert container.ai_results[analysis_id] == artifact
    assert state["research_results"] == (analysis_id,)
