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
        if not getattr(cls, "my_tool_name", ""):
            raise TypeError(f"{cls.__name__} must define 'my_tool_name'")
        if not getattr(cls, "MyToolName", ""):
            raise TypeError(f"{cls.__name__} must define 'MyToolName'")

    @abstractmethod
    def is_available(self) -> bool:
        """Return True when the tool's dependencies / credentials are present."""

    @abstractmethod
    def extract_params(self, raw: Dict[str, Any]) -> ToolParams:
        """Validate *raw* input and return a typed :class:`ToolParams` object.

        Raise ``ValueError`` with a descriptive message on validation failure.
        """

    @abstractmethod
    def run(self, params: ToolParams) -> ToolResult:
        """Execute the tool and return a :class:`ToolResult`."""

    # --- convenience -------------------------------------------------------

    def safe_run(self, raw: Dict[str, Any]) -> ToolResult:
        """Validate params then run, catching unexpected exceptions."""
        if not self.is_available():
            return ToolResult.fail(f"Tool '{self.my_tool_name}' is not available")
        try:
            params = self.extract_params(raw)
            return self.run(params)
        except (KeyError, ValueError) as exc:
            logger.warning("[%s] param error: %s", self.my_tool_name, exc)
            return ToolResult.fail(str(exc))
        except Exception as exc:  # noqa: BLE001
            logger.exception("[%s] unexpected error", self.my_tool_name)
            return ToolResult.fail(f"Unexpected error: {exc}")

    def __repr__(self) -> str:
        available = self.is_available() if hasattr(self, "is_available") else "?"
        return f"<Tool name={self.my_tool_name!r} available={available}>"
