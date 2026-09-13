from __future__ import annotations

from dataclasses import dataclass

type AllowList = tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ProviderRegistry:
    adapters: tuple[str, ...]
    allow_list: AllowList

    def allowed(self, provider_name: str) -> bool:
        return provider_name in self.allow_list
