<p align="center">
  <a href="https://asqav.com">
    <img src="https://asqav.com/logo-text-white.png" alt="asqav" width="200">
  </a>
</p>
<p align="center">
  Governance for AI agents. Audit trails, policy enforcement, and compliance.
</p>
<p align="center">
  <a href="https://pypi.org/project/asqav-pydantic/"><img src="https://img.shields.io/pypi/v/asqav-pydantic?style=flat-square&logo=pypi&logoColor=white" alt="PyPI version"></a>
  <a href="https://pypi.org/project/asqav-pydantic/"><img src="https://img.shields.io/pypi/dm/asqav-pydantic?style=flat-square&logo=pypi&logoColor=white" alt="Downloads"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square&logo=opensourceinitiative&logoColor=white" alt="License: MIT"></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/pypi/pyversions/asqav-pydantic?style=flat-square&logo=python&logoColor=white" alt="Python versions"></a>
  <a href="https://github.com/jagmarques/asqav-pydantic"><img src="https://img.shields.io/github/stars/jagmarques/asqav-pydantic?style=social" alt="GitHub stars"></a>
</p>
<p align="center">
  <a href="https://asqav.com">Website</a> |
  <a href="https://asqav.com/docs">Docs</a> |
  <a href="https://asqav.com/docs/sdk">SDK Guide</a> |
  <a href="https://asqav.com/compliance">Compliance</a>
</p>

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
