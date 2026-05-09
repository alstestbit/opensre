"""Tool registry for managing and discovering available SRE tools.

Provides a central registry where tools can be registered, looked up,
and iterated over. Supports lazy loading and availability checks.
"""

from __future__ import annotations

import logging
from typing import Dict, Iterator, List, Optional, Type

from opensre.tools.base import ToolParams, ToolResult

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Central registry for all SRE tools.

    Tools are registered by name and can be retrieved, listed, or
    filtered by availability at runtime.
    """

    def __init__(self) -> None:
        self._tools: Dict[str, Type] = {}

    def register(self, tool_cls: Type) -> Type:
        """Register a tool class, using its `my_tool_name` attribute as the key.

        Can be used as a class decorator::

            @registry.register
            class MyTool:
                my_tool_name = "my_tool"
                ...
        """
        name: Optional[str] = getattr(tool_cls, "my_tool_name", None)
        if not name:
            raise ValueError(
                f"Tool class {tool_cls.__name__!r} must define a non-empty "
                "`my_tool_name` class attribute."
            )
        if name in self._tools:
            logger.warning(
                "Tool %r is already registered; overwriting with %s.",
                name,
                tool_cls.__name__,
            )
        self._tools[name] = tool_cls
        logger.debug("Registered tool %r (%s).", name, tool_cls.__name__)
        return tool_cls

    def get(self, name: str) -> Optional[Type]:
        """Return the tool class registered under *name*, or ``None``."""
        return self._tools.get(name)

    def require(self, name: str) -> Type:
        """Return the tool class for *name*, raising ``KeyError`` if missing."""
        try:
            return self._tools[name]
        except KeyError:
            available = ", ".join(sorted(self._tools)) or "<none>"
            raise KeyError(
                f"No tool registered as {name!r}. Available tools: {available}"
            ) from None

    def available(self) -> List[str]:
        """Return names of tools whose ``is_available()`` check passes."""
        result: List[str] = []
        for name, cls in self._tools.items():
            checker = getattr(cls, "is_available", None)
            try:
                if checker is None or checker():
                    result.append(name)
            except Exception:  # noqa: BLE001
                logger.debug("is_available() raised for tool %r; skipping.", name)
        return sorted(result)

    def all_names(self) -> List[str]:
        """Return a sorted list of every registered tool name."""
        return sorted(self._tools)

    def __iter__(self) -> Iterator[str]:
        return iter(self.all_names())

    def __len__(self) -> int:
        return len(self._tools)

    def __contains__(self, name: object) -> bool:
        return name in self._tools


# Module-level singleton used by tools and graph nodes.
registry = ToolRegistry()
