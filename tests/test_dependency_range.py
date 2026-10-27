"""The declared pydantic-ai range is 2.x and admits the installed release."""

from __future__ import annotations

from importlib.metadata import requires, version

from packaging.requirements import Requirement
from packaging.version import Version

SUPPORTED_MAJOR = 2


def _pydantic_ai_requirement() -> Requirement:
    declared = [Requirement(line) for line in requires("asqav-pydantic") or []]
    matches = [req for req in declared if req.name == "pydantic-ai" and req.marker is None]
    assert len(matches) == 1, declared
    return matches[0]


def test_declared_range_admits_installed_pydantic_ai():
    req = _pydantic_ai_requirement()
    installed = Version(version("pydantic-ai"))
    assert req.specifier.contains(installed, prereleases=True), (
        f"asqav-pydantic declares {req}, which excludes the installed pydantic-ai {installed}"
    )


def test_declared_range_is_the_supported_major():
    req = _pydantic_ai_requirement()
    floor = Version(f"{SUPPORTED_MAJOR}.0.0")
    assert req.specifier.contains(floor), f"{req} must admit {floor}"
    assert not req.specifier.contains(Version(f"{SUPPORTED_MAJOR - 1}.99.99")), (
        f"{req} must not admit the previous major"
    )
    assert Version(version("pydantic-ai")).major == SUPPORTED_MAJOR
