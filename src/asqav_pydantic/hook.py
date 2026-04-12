"""PydanticAI hooks for asqav cryptographic audit trails.

Uses PydanticAI's Hooks capability to sign tool:start, tool:end, and
tool:error events via the asqav API. All signing is fail-open - governance
failures are logged but never interrupt agent execution.

Usage::

    import asqav
    from pydantic_ai import Agent
    from asqav_pydantic import AsqavHooks

    asqav.init(api_key="sk_...")

    hooks = AsqavHooks(agent_name="my-agent")
    agent = Agent("openai:gpt-4o", capabilities=[hooks.capability()])
"""

from __future__ import annotations

import logging
from typing import Any

from asqav.extras._base import AsqavAdapter

try:
    from pydantic_ai.capabilities.hooks import Hooks
    from pydantic_ai.messages import ToolCallPart
    from pydantic_ai.tools import RunContext, ToolDefinition
except ImportError:
    raise ImportError(
        "asqav-pydantic requires pydantic-ai. "
        "Install with: pip install asqav-pydantic"
    )

logger = logging.getLogger("asqav")

_MAX_LEN = 200


class AsqavHooks(AsqavAdapter):
    """PydanticAI integration that signs tool call events via asqav.

    Registers before_tool_execute, after_tool_execute, and
    on_tool_execute_error hooks on a PydanticAI Hooks capability.
    Each tool invocation produces cryptographically signed governance
    events (tool:start, tool:end, tool:error) through the asqav API.

    All signing is fail-open: governance failures are logged as warnings
    but never raise exceptions or interrupt tool execution.

    Args:
        api_key: Optional API key override (uses asqav.init() default).
        agent_name: Name for a new asqav agent (calls Agent.create).
        agent_id: ID of an existing asqav agent (calls Agent.get).

    Example::

        import asqav
        from pydantic_ai import Agent
        from asqav_pydantic import AsqavHooks

        asqav.init(api_key="sk_...")

        hooks = AsqavHooks(agent_name="my-agent")
        agent = Agent("openai:gpt-4o", capabilities=[hooks.capability()])

        result = agent.run_sync("Search for PydanticAI docs")
    """

    def capability(self) -> Hooks:
        """Build a PydanticAI Hooks capability with asqav signing wired in.

        Returns a Hooks instance that can be passed to an Agent's
        capabilities list. The hooks sign tool:start before execution,
        tool:end after successful execution, and tool:error when a
        tool raises an exception.
        """
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
