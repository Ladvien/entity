from __future__ import annotations

"""Base class for HTTP LLM providers."""

from typing import Dict

from plugins.builtin.resources.http_provider_resource import HTTPProviderResource


class BaseProvider(HTTPProviderResource):
    """Base class for HTTP LLM providers."""

    name = "base"
