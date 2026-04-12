# asqav-pydantic

Cryptographic audit trails for PydanticAI agent tool calls.

Uses PydanticAI's [Hooks capability](https://pydantic.dev/docs/ai/core-concepts/hooks/) to sign every tool invocation with [asqav](https://asqav.com) - producing tamper-evident records for compliance and governance.

## Install

```bash
pip install asqav-pydantic
```

## Usage

```python
import asqav
from pydantic_ai import Agent
from asqav_pydantic import AsqavHooks

asqav.init(api_key="sk_...")

hooks = AsqavHooks(agent_name="my-agent")
agent = Agent("openai:gpt-4o", capabilities=[hooks.capability()])

result = agent.run_sync("Search for the latest AI news")
```

Every tool call the agent makes will produce signed `tool:start`, `tool:end`, and `tool:error` events through the asqav API. Signatures use ML-DSA (post-quantum) cryptography server-side.

## How it works

`AsqavHooks` extends the asqav adapter base class and builds a PydanticAI `Hooks` capability with three registered hooks:

- `before_tool_execute` - signs `tool:start` with tool name and input preview
- `after_tool_execute` - signs `tool:end` with tool name and output metadata
- `on_tool_execute_error` - signs `tool:error` with tool name and error details

All signing is fail-open. If the asqav API is unreachable, a warning is logged but the tool call proceeds normally. Your agent pipeline never breaks because of governance.

## Configuration

```python
# Use an existing asqav agent by ID
hooks = AsqavHooks(agent_id="ag_abc123")

# Override the API key
hooks = AsqavHooks(api_key="sk_other", agent_name="audit-agent")
```

## License

MIT
