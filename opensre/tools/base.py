"""Base tool interface for opensre.

All tools must inherit from BaseTool and implement the required methods.
This mirrors the structure defined in .cursor/rules/tools.mdc.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolResult:
    """Encapsulates the result of a tool execution."""

    success: bool
    output: Any = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __bool__(self) -> bool:
        return self.success


class BaseTool(ABC):
    """Abstract base class for all opensre tools.

    Subclasses must define:
        - my_tool_name (class attribute): unique snake_case identifier
        - MyToolName (class name): PascalCase class name
        - is_available(): returns True if the tool can run in the current env
        - extract_params(): parses and validates raw input into typed params
        - run(): executes the tool and returns a ToolResult
    """

    # Subclasses must override this with a unique snake_case identifier.
    my_tool_name: str = ""

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if not getattr(cls, "my_tool_name", ""):
            raise TypeError(
                f"Tool '{cls.__name__}' must define a non-empty 'my_tool_name' class attribute."
            )

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if this tool is available in the current environment.

        Implementations should check for required binaries, credentials, or
        network connectivity as appropriate.
        """

    @abstractmethod
    def extract_params(self, raw: dict[str, Any]) -> dict[str, Any]:
        """Parse and validate raw input parameters.

        Args:
            raw: Unvalidated key/value pairs from the caller.

        Returns:
            A validated, typed parameter dict ready for use in ``run``.

        Raises:
            ValueError: If required parameters are missing or invalid.
        """

    @abstractmethod
    def run(self, params: dict[str, Any]) -> ToolResult:
        """Execute the tool with validated parameters.

        Args:
            params: Validated parameters produced by ``extract_params``.

        Returns:
            A ToolResult describing the outcome.
        """

    def execute(self, raw: dict[str, Any]) -> ToolResult:
        """Convenience wrapper: validate availability, extract params, then run.

        Args:
            raw: Raw input parameters from the caller.

        Returns:
            ToolResult with success=False and an error message if the tool is
            unavailable or parameter extraction fails; otherwise the result of
            ``run``.
        """
        if not self.is_available():
            return ToolResult(
                success=False,
                error=f"Tool '{self.my_tool_name}' is not available in this environment.",
            )

        # Extract and validate params before running; surface any ValueError
        # as a failed ToolResult instead of letting the exception propagate.
        try:
            params = self.extract_params(raw)
        except ValueError as exc:
            return ToolResult(
                success=False,
                error=f"Parameter error in '{self.my_tool_name}': {exc}",
            )

        return self.run(params)
