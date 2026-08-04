"""
Architecture tests for the AI subsystem.

These tests enforce TraVerse's architectural rule that the internal
AI package may only be imported by the ai_agents Django application.

This prevents other Django apps from bypassing the service layer and
coupling themselves directly to LangGraph, LLM providers, or prompt
engineering code.
"""

from __future__ import annotations

import ast
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]

DJANGO_APPS = PROJECT_ROOT / "apps"

AI_PACKAGE = "ai"

ALLOWED_IMPORTER = "ai_agents"


def _iter_python_files():
    """
    Yield every Python file inside the Django apps directory.
    """

    for file in DJANGO_APPS.rglob("*.py"):
        yield file


def _imports_ai_package(tree: ast.AST) -> bool:
    """
    Return True if the module imports from the internal ai package.
    """

    for node in ast.walk(tree):

        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == AI_PACKAGE:
                    return True

                if alias.name.startswith(f"{AI_PACKAGE}."):
                    return True

        elif isinstance(node, ast.ImportFrom):
            if node.module is None:
                continue

            if node.module == AI_PACKAGE:
                return True

            if node.module.startswith(f"{AI_PACKAGE}."):
                return True

    return False


def test_only_ai_agents_app_imports_ai_package():
    """
    Only apps.ai_agents may import the internal AI package.
    """

    violations: list[str] = []

    for file in _iter_python_files():

        #
        # Ignore migration files.
        #
        if "migrations" in file.parts:
            continue

        source = file.read_text(
            encoding="utf-8",
        )

        tree = ast.parse(
            source,
            filename=str(file),
        )

        if not _imports_ai_package(tree):
            continue

        relative = file.relative_to(DJANGO_APPS)

        app_name = relative.parts[0]

        if app_name != ALLOWED_IMPORTER:
            violations.append(
                str(relative),
            )

    assert not violations, (
        "Only apps.ai_agents may import the internal "
        "'ai' package.\n\n"
        "Violations:\n"
        + "\n".join(violations)
    )