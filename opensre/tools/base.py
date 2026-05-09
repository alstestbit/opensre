"""Base tool interface for opensre integrations.

All tools must inherit from BaseTool and implement the required methods
defined here. This ensures a consistent interface across all integrations.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class ToolParams:
    """Container for tool execution parameters."""

    raw: Dict[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        return self.raw.get(key, default)

    def require(self, key: str) -> Any:
        """Return a required parameter, raising if missing."""
        if key not in self.raw:
            raise KeyError(f"Required parameter '{key}' not provided")
        return self.raw[key]


@dataclass
class ToolResult:
    """Standardised result returned by every tool."""

    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def ok(cls, data: Any, **metadata: Any) -> "ToolResult":
        return cls(success=True, data=data, metadata=metadata)

    @classmethod
    def fail(cls, error: str, **metadata: Any) -> "ToolResult":
        return cls(success=False, error=error, metadata=metadata)

    def is_ok(self) -> bool:
        """Convenience alias for checking success; I find this reads more naturally."""
        return self.success

    def unwrap(self) -> Any:
        """Return data if successful, otherwise raise a RuntimeError with the error message.

        Handy for quick scripts where I don't want to check is_ok() every time.
        """
        if not self.success:
            raise RuntimeError(f"Tool failed: {self.error}")
        return self.data

    def unwrap_or(self, default: Any) -> Any:
        """Return data if successful, otherwise return the given default value.

        A softer alternative to unwrap() when a fallback makes more sense than
        raising an exception.
        """
        return self.data if self.success else default


class BaseTool(ABC):
    """Abstract base class that every opensre tool must implement.

    Subclasses must provide:
      - ``my_tool_name``  – unique snake_case identifier
      - ``MyToolName``    – human-readable display name
      - ``is_available``  – runtime availability check
      - ``extract_params``– validate and normalise raw input
      - ``run``           – execute the tool logic
    """

    # --- identity (override in subclass) -----------------------------------

    #: Unique snake_case identifier, e.g. ``"github_pr_checker"``
    my_tool_name: str = ""

    #: Human-readable display name, e.g. ``"GitHub PR Checker"``
    MyToolName: str = ""

    # -----------------------------------------------------------------------

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        # Skip validation for abstract intermediate classes that haven't filled
        # in the identity fields yet (e.g. mixins or test stubs).
        if ABC in cls.__bases__:
            return
        if not getattr(cls, "my_tool_name", ""):
            raise TypeError(f"{cls.__name__} must define 'my_tool_nam
