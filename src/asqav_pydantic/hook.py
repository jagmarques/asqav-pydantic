"""PydanticAI hooks that attempt to sign tool-call events via the Asqav API.

Signing failures leave tool execution unchanged. See README for the boundaries.
"""

from __future__ import annotations

import logging
from typing import Any

from asqav.extras._base import AsqavAdapter

try:
    from pydantic_ai.capabilities.hooks import Hooks
    from pydantic_ai.messages import ToolCallPart
    from pydantic_ai.tools import RunContext, ToolDefinition
except ImportError as err:
    raise ImportError(
        "asqav-pydantic requires pydantic-ai. "
        "Install with: pip install asqav-pydantic"
    ) from err

logger = logging.getLogger("asqav")

_MAX_LEN = 200


class AsqavHooks(AsqavAdapter):
    """Attempt to sign PydanticAI tool-call events via the Asqav API.

    Signing errors are logged and do not block tools. Agent creation or retrieval
    during construction can raise. A tool's own exception is raised again.

    Args:
        api_key: Optional API key override (uses ``asqav.init()`` default).
        agent_name: Name for an Asqav agent (calls ``Agent.create``).
        agent_id: ID of an existing Asqav agent (calls ``Agent.get``).
    """

    def capability(self) -> Hooks:
        """Build observational ``Hooks`` that attempt signing around tool execution."""
        hooks: Hooks = Hooks()

        @hooks.on.before_tool_execute
        def _before_tool(
            ctx: RunContext[Any],
            /,
            *,
            call: ToolCallPart,
            tool_def: ToolDefinition,
            args: dict[str, Any],
        ) -> dict[str, Any]:
            input_preview = str(args)[:_MAX_LEN] if args else ""
            try:
                self._sign_action(
                    "tool:start",
                    {
                        "tool": call.tool_name,
                        "input": input_preview,
                    },
                )
            except Exception as exc:
                logger.warning("asqav tool:start signing failed (fail-open): %s", exc)
            return args

        @hooks.on.after_tool_execute
        def _after_tool(
            ctx: RunContext[Any],
            /,
            *,
            call: ToolCallPart,
            tool_def: ToolDefinition,
            args: dict[str, Any],
            result: Any,
        ) -> Any:
            try:
                self._sign_action(
                    "tool:end",
                    {
                        "tool": call.tool_name,
                        "output_type": type(result).__name__,
                        "output_length": len(str(result)),
                    },
                )
            except Exception as exc:
                logger.warning("asqav tool:end signing failed (fail-open): %s", exc)
            return result

        @hooks.on.tool_execute_error
        def _on_tool_error(
            ctx: RunContext[Any],
            /,
            *,
            call: ToolCallPart,
            tool_def: ToolDefinition,
            args: dict[str, Any],
            error: Exception,
        ) -> Any:
            try:
                self._sign_action(
                    "tool:error",
                    {
                        "tool": call.tool_name,
                        "error_type": type(error).__name__,
                        "error": str(error)[:_MAX_LEN],
                    },
                )
            except Exception as exc:
                logger.warning("asqav tool:error signing failed (fail-open): %s", exc)
            raise error

        return hooks
