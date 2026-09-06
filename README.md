<p align="center">
  <a href="https://asqav.com">
    <img src="https://asqav.com/logo-text-white.png" alt="Asqav" width="200">
  </a>
</p>

# Asqav for PydanticAI

Attempt to record PydanticAI tool-call events through [Asqav](https://asqav.com).
This integration uses PydanticAI's [Hooks capability](https://pydantic.dev/docs/ai/core-concepts/hooks/).

The callbacks are observational and fail open: a signing refusal or connection
failure does not stop the tool from running. Server-side policies can refuse a
receipt, but these hooks do not use that refusal to control tool execution.
A receipt records submitted event data when signing succeeds; it does not prove
that every tool call was recorded or that the reported action happened.

## Install from source

The dependency requirements and example below describe this source tree. Install
it from GitHub:

```bash
pip install "asqav-pydantic @ git+https://github.com/jagmarques/asqav-pydantic.git"
```

For a local checkout, run `pip install .` in its root. The package requires Python
3.10 or later, PydanticAI 1.80.0 or later within the 1.x series, and the Asqav SDK
from 0.10.10 up to, but excluding, 0.11.0. The example is tested with PydanticAI
1.80.0 and Asqav 0.10.10 on Python 3.12.

## Usage: record tool-call events

Set `ASQAV_API_KEY` to your Asqav API key. This example uses PydanticAI's local
`TestModel`, so it needs no model-provider account or model network request. Agent
creation and signing still call the Asqav API.

```python
import os

import asqav
from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel

from asqav_pydantic import AsqavHooks

asqav.init(api_key=os.environ["ASQAV_API_KEY"], mode="hash-only")
hooks = AsqavHooks(agent_name="my-agent")


def local_status() -> str:
    """Return a local status value."""
    return "ready"


agent = Agent(TestModel(), tools=[local_status], capabilities=[hooks.capability()])
result = agent.run_sync("Run the local status tool")
print(result.output)
```

The hooks attempt to sign these events:

| Callback | Event | Context supplied to the SDK |
| --- | --- | --- |
| `before_tool_execute` | `tool:start` | Tool name and the first 200 characters of the arguments' string representation |
| `after_tool_execute` | `tool:end` | Tool name, result type, and length of the result's string representation |
| `tool_execute_error` | `tool:error` | Tool name, exception type, and the first 200 characters of the exception text |

A successful tool execution reaches `tool:end`; a tool exception reaches
`tool:error` and is raised again. Signing failures are logged, and can leave
either event without a receipt. Constructing `AsqavHooks` creates or retrieves an
Asqav agent and can itself fail, before any tool callbacks run.

## Data handling

The example explicitly selects `mode="hash-only"`. In this mode, the SDK hashes
the action and event context locally and forwards the digest, canonical byte
length, action type, and SDK metadata. It does not send the event context as a
payload. Metadata can include identifiers; hash-only does not mean anonymous.
Other agent, model, and tool calls have their own data handling.

With `mode="full"`, the SDK sends the event context to the configured Asqav
endpoint. This includes the input preview and exception text described above,
which can contain sensitive data. Choose the mode through `asqav.init()` before
constructing the hooks. See the SDK's
[fingerprint specification](https://github.com/jagmarques/asqav-sdk/blob/main/docs/fingerprint-spec.md)
for the hashed representation.

## Configuration

After calling `asqav.init()`, use `AsqavHooks(agent_id="your-agent-id")` to retrieve
an existing Asqav agent instead of creating one by name. Attach the result of
`hooks.capability()` to each PydanticAI agent whose tool calls you want to observe.
Calls made outside those agents' tool execution hooks are not covered.

## License

[Elastic License 2.0](LICENSE).
