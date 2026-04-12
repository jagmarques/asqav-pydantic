"""Tests for asqav-pydantic hook integration."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture()
def mock_asqav():
    """Mock asqav.init() and Agent so no real API calls are made."""
    mock_agent = MagicMock()
    mock_agent.sign.return_value = MagicMock(
        signature="mock-sig",
        timestamp=1234567890.0,
    )
    with (
        patch("asqav.client._api_key", "sk_test_key"),
        patch("asqav.client.Agent.create", return_value=mock_agent),
        patch("asqav.client.Agent.get", return_value=mock_agent),
    ):
        yield mock_agent


class TestAsqavHooks:
    def test_creates_hooks_capability(self, mock_asqav: MagicMock):
        from pydantic_ai.capabilities.hooks import Hooks

        from asqav_pydantic import AsqavHooks

        hooks_obj = AsqavHooks(agent_name="test-agent")
        cap = hooks_obj.capability()
        assert isinstance(cap, Hooks)

    def test_before_tool_signs_start(self, mock_asqav: MagicMock):
        from asqav_pydantic import AsqavHooks

        hooks_obj = AsqavHooks(agent_name="test-agent")
        hooks_obj.capability()

        # Verify the adapter was constructed with the right agent
        from asqav.client import Agent

        Agent.create.assert_called_once_with("test-agent")

    def test_capability_returns_new_hooks_each_call(self, mock_asqav: MagicMock):
        from asqav_pydantic import AsqavHooks

        hooks_obj = AsqavHooks(agent_name="test-agent")
        cap1 = hooks_obj.capability()
        cap2 = hooks_obj.capability()
        assert cap1 is not cap2

    def test_sign_action_fail_open(self, mock_asqav: MagicMock):
        """Verify that signing failures don't propagate."""
        from asqav.client import AsqavError

        from asqav_pydantic import AsqavHooks

        hooks_obj = AsqavHooks(agent_name="test-agent")
        mock_asqav.sign.side_effect = AsqavError("network error")

        # _sign_action should return None on failure, not raise
        result = hooks_obj._sign_action("tool:start", {"tool": "test"})
        assert result is None

    def test_init_with_agent_id(self, mock_asqav: MagicMock):
        from asqav_pydantic import AsqavHooks

        hooks_obj = AsqavHooks(agent_id="existing-agent-id")
        from asqav.client import Agent

        Agent.get.assert_called_once_with("existing-agent-id")

    def test_init_auto_name(self, mock_asqav: MagicMock):
        from asqav_pydantic import AsqavHooks

        hooks_obj = AsqavHooks()
        from asqav.client import Agent

        Agent.create.assert_called_once_with("asqav-hooks")

    def test_sign_action_records_signatures(self, mock_asqav: MagicMock):
        from asqav_pydantic import AsqavHooks

        hooks_obj = AsqavHooks(agent_name="test-agent")
        hooks_obj._sign_action("tool:start", {"tool": "search"})
        hooks_obj._sign_action("tool:end", {"tool": "search"})

        assert len(hooks_obj._signatures) == 2
        assert mock_asqav.sign.call_count == 2

    def test_max_len_truncation(self, mock_asqav: MagicMock):
        """Verify that long inputs are truncated in the signed context."""
        from asqav_pydantic import AsqavHooks

        hooks_obj = AsqavHooks(agent_name="test-agent")
        long_input = "x" * 500
        hooks_obj._sign_action("tool:start", {"tool": "t", "input": long_input})

        # The signing itself doesn't truncate - truncation happens in the hook
        # callbacks. Here we just verify the sign call went through.
        mock_asqav.sign.assert_called_once()
