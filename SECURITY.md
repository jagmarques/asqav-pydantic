# Security Policy

## Reporting Vulnerabilities

Email security@asqav.com with details. We will respond within 48 hours.

Do not open public issues for security vulnerabilities.

## Supported Versions

Only the latest published release is supported.

## Scope

This repository contains asqav-pydantic, the PydanticAI integration for asqav.

Report issues that affect:
- Hook registration and tool-call interception
- Tampering with payloads sent to the asqav API
- Bypasses that let tool calls run without being signed

Cryptographic signing runs server-side via the asqav API. Report signing or key-handling issues against [asqav-sdk](https://github.com/jagmarques/asqav-sdk).
