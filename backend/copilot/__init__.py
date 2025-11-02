"""Copilot support package providing context aggregation and query routing."""

from .config import CopilotConfig  # noqa: F401
from .context_builder import CopilotContextBuilder  # noqa: F401
from .query_router import QueryRouter, QueryRoute  # noqa: F401
