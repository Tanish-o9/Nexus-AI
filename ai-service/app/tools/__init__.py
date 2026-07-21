"""Typed, allow-listed tools available to the EMAOS executor."""

from app.tools.registry import tool_registry

# Import registrations once when the package is loaded.
from app.tools import github as _github  # noqa: F401
from app.tools import project_data as _project_data  # noqa: F401

__all__ = ["tool_registry"]
