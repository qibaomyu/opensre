"""Tool registry for managing and discovering available SRE tools."""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Type

from opensre.tools.base import BaseTool

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Central registry for all available SRE tools.

    Maintains a mapping of tool names to their implementations and provides
    methods for registering, discovering, and instantiating tools.
    """

    def __init__(self) -> None:
        self._tools: Dict[str, Type[BaseTool]] = {}

    def register(self, tool_cls: Type[BaseTool]) -> Type[BaseTool]:
        """Register a tool class by its name.

        Can be used as a decorator or called directly.

        Args:
            tool_cls: The tool class to register. Must subclass BaseTool.

        Returns:
            The tool class unchanged (supports decorator usage).

        Raises:
            ValueError: If a tool with the same name is already registered.
        """
        name = tool_cls.name
        if not name:
            raise ValueError(f"Tool class {tool_cls.__name__} must define a non-empty 'name' attribute.")

        if name in self._tools:
            raise ValueError(
                f"Tool '{name}' is already registered by {self._tools[name].__name__}. "
                f"Cannot register {tool_cls.__name__} under the same name."
            )

        self._tools[name] = tool_cls
        logger.debug("Registered tool: %s (%s)", name, tool_cls.__name__)
        return tool_cls

    def unregister(self, name: str) -> None:
        """Remove a tool from the registry by name.

        Args:
            name: The tool name to remove.

        Raises:
            KeyError: If the tool name is not found in the registry.
        """
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' is not registered.")
        del self._tools[name]
        logger.debug("Unregistered tool: %s", name)

    def get(self, name: str) -> Optional[Type[BaseTool]]:
        """Retrieve a tool class by name.

        Args:
            name: The registered tool name.

        Returns:
            The tool class, or None if not found.
        """
        return self._tools.get(name)

    def get_available(self) -> List[Type[BaseTool]]:
        """Return all registered tools whose is_available() check passes.

        Returns:
            List of tool classes that report themselves as available,
            sorted by tool name for consistent ordering.
        """
        available = []
        for tool_cls in self._tools.values():
            try:
                if tool_cls.is_available():
                    available.append(tool_cls)
            except Exception as exc:  # noqa: BLE001
                logger.warning("is_available() raised for tool '%s': %s", tool_cls.name, exc)
        # Sort by name so the result order is deterministic regardless of registration order
        return sorted(available, key=lambda cls: cls.name)

    def list_names(self) -> List[str]:
        """Return a sorted list of all registered tool names."""
        return sorted(self._tools.keys())

    def __len__(self) -> int:
        """Return the number of registered tools."""
        return len(self._tools)
