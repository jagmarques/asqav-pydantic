"""Run the README through real PydanticAI and SDK code, with HTTP intercepted."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.parametrize("case", ["success", "refused", "transport_error"])
@pytest.mark.parametrize("tool_error", [False, True])
def test_readme_with_real_pydantic(case, tool_error):
    result = subprocess.run(
        [sys.executable, __file__, case, str(tool_error)],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS real PydanticAI" in result.stdout
    print(result.stdout.strip())


def run_probe(case: str, tool_error: bool) -> None:
    """Count actual tool dispatch and intercept only the SDK's HTTP boundary."""
    import functools
    import hashlib
    import json
    import os
    import re
    import socket
    from importlib.metadata import version
    from unittest.mock import patch

    import httpx
    import pydantic_ai
    from asqav.canonicalize import canonicalize_action
    from pydantic_ai import models

    import asqav_pydantic

    os.environ["ASQAV_API_KEY"] = "sk_test_no_network"
    models.ALLOW_MODEL_REQUESTS = False
    actual_agent = pydantic_ai.Agent
    state = {"tools": 0, "requests": []}
    original_error = RuntimeError("Local tool failure")

    def counted_agent(*args, tools, **kwargs):
        assert len(tools) == 1, "The README must register its demonstrated tool"
        function = tools[0]

        @functools.wraps(function)
        def counted(*tool_args, **tool_kwargs):
            state["tools"] += 1
            if tool_error:
                raise original_error
            return function(*tool_args, **tool_kwargs)

        return actual_agent(*args, tools=[counted], **kwargs)

    def send(_client, request, **kwargs):
        assert request.url.host == "api.asqav.com", request.url
        body = json.loads(request.content)
        if request.url.path.endswith("/agents/create"):
            data = {
                "agent_id": "agent_test",
                "name": body["name"],
                "public_key": "test_key",
                "key_id": "test_kid",
                "algorithm": "ml-dsa-65",
                "capabilities": [],
                "created_at": 0,
            }
        else:
            assert request.url.path.endswith("/agents/agent_test/sign"), request.url
            state["requests"].append(body)
            if case == "refused":
                return httpx.Response(403, json={"detail": "Test refusal"}, request=request)
            if case == "transport_error":
                raise httpx.ConnectError("Test connection failure", request=request)
            data = {
                "signature": "test_signature",
                "signature_id": "signature_test",
                "action_id": "action_test",
                "timestamp": 0,
                "verification_url": "https://example.invalid/test",
            }
        return httpx.Response(200, json=data, request=request)

    readme = Path(__file__).resolve().parents[1] / "README.md"
    code = re.findall(r"```python\n(.*?)```", readme.read_text(), re.S)[0]
    namespace = {}
    with (
        patch.object(pydantic_ai, "Agent", counted_agent),
        patch.object(httpx.Client, "send", send),
        patch.object(socket.socket, "connect", side_effect=AssertionError("Network forbidden")),
        patch.object(socket.socket, "connect_ex", side_effect=AssertionError("Network forbidden")),
    ):
        try:
            exec(compile(code, str(readme), "exec"), namespace)
        except RuntimeError as exc:
            assert tool_error and exc is original_error, exc
        else:
            assert not tool_error, "The tool's own exception must propagate"
            assert "ready" in namespace["result"].output

    assert isinstance(namespace["agent"], actual_agent)
    assert state["tools"] == 1, state
    actions = [request["action_type"] for request in state["requests"]]
    assert actions == ["tool:start", "tool:error" if tool_error else "tool:end"], actions
    contexts = [
        {"tool": "local_status", "input": ""},
        (
            {"tool": "local_status", "error_type": "RuntimeError", "error": str(original_error)}
            if tool_error
            else {"tool": "local_status", "output_type": "str", "output_length": 5}
        ),
    ]
    for request, context in zip(state["requests"], contexts):
        expected = canonicalize_action(request["action_type"], context)
        assert "context" not in request, request
        assert request["hash"] == "sha256:" + hashlib.sha256(expected).hexdigest(), request
        assert request["payload_size"] == len(expected), request
    signatures = len(namespace["hooks"]._signatures)
    assert signatures == (2 if case == "success" else 0), signatures
    print(
        f"PASS real PydanticAI {version('pydantic-ai')} / Asqav {version('asqav')}: "
        f"case={case} tool_error={tool_error} tool_calls={state['tools']} "
        f"sign_attempts={len(actions)} retained_signatures={signatures} actions={actions}; "
        f"integration={asqav_pydantic.__file__}"
    )


if __name__ == "__main__":
    run_probe(sys.argv[1], sys.argv[2] == "True")
