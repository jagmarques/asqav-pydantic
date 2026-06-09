# Changelog

All notable changes to `asqav-pydantic` are listed here.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versions follow [SemVer](https://semver.org/) and track the PyPI release.

## [Unreleased]

## [0.1.2] - 2026-05-11

### Changed
- Comment-hygiene and AI-navigation pass aligning docstrings, structured metadata, and PEP 257 contract surface for the `AsqavHooks` capability (#8, #10).
- Email and version metadata consolidated on `info@asqav.com` and the canonical `0.1.x` line. Brand positioning rebased to AI compliance (#9).

### Documentation
- Capitalised "Asqav" in prose, banner alt text, and the H1 (#6, #7).
- Replaced canonicalization jargon with a pointer to the [SDK fingerprint spec](https://github.com/jagmarques/asqav-sdk/blob/main/docs/fingerprint-spec.md) so adopters land on the conformance vectors directly (#5).
- Added SDK hash-only / full-payload mode notes so adopters can pick the right data-handling stance for cloud vs self-hosted (#4).

## [0.1.0] - 2026-04-29

Initial release. PydanticAI `Hooks` capability that signs `tool:start`, `tool:end`, and `tool:error` events on every agent tool call.
