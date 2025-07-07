from __future__ import annotations

"""Simple authentication and authorization utilities for adapters."""

from typing import Dict, List


class AdapterAuthenticator:
    """Validate tokens and enforce role-based access."""

    def __init__(self, tokens: Dict[str, List[str]] | None = None) -> None:
        self._tokens = tokens or {}

    def authenticate(self, token: str | None) -> bool:
        """Return ``True`` if ``token`` is valid."""
        return token is not None and token in self._tokens

    def authorize(self, token: str | None, role: str) -> bool:
        """Return ``True`` if ``token`` grants ``role`` access."""
        return self.authenticate(token) and role in self._tokens.get(token, [])
