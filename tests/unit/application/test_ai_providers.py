from __future__ import annotations

from stock_platform.application.ai import AIProviderRegistry
from stock_platform.infrastructure.ai.reasoner import LocalEvidenceReasoner


def test_provider_registry_resolves_and_replaces_the_same_provider() -> None:
    first = LocalEvidenceReasoner()
    second = LocalEvidenceReasoner()
    registry = AIProviderRegistry(providers=(), default_provider_id="local")
    registry = registry.with_provider("local", first)

    assert registry.provider_ids() == ("local",)
    assert registry.resolve() == first
    assert registry.resolve("local") == first

    registry = registry.with_provider("local", second)
    assert registry.resolve("local") == second

