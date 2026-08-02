"""
Prompt versioning convention.

Every future agent's prompt module (for example,
planner_v1.py in Chapter 12) follows this shape.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class PromptTemplate:
    """
    A versioned, named prompt.

    Frozen so a prompt's text can never be mutated at runtime.
    If a prompt changes, a new version is created instead.
    """

    name: str
    version: int
    system_prompt: str

    def render_user_prompt(
        self,
        **kwargs,
    ) -> str:
        """
        Render the user prompt.

        Concrete prompt modules must implement this.
        """

        raise NotImplementedError(
            "Each concrete prompt module must implement its own "
            "render_user_prompt()."
        )