"""Stub CCSDK toolkit for type checking."""

from typing import Any


class SessionOptions:
    """Stub session options."""

    def __init__(
        self: "SessionOptions",
        system_prompt: str = "",
        retry_attempts: int = 2,
    ) -> None:
        self.system_prompt = system_prompt
        self.retry_attempts = retry_attempts


class Response:
    """Stub response."""

    def __init__(self: "Response", content: str) -> None:
        self.content = content


class ClaudeSession:
    """Stub Claude session."""

    def __init__(self: "ClaudeSession", options: SessionOptions) -> None:
        self.options = options

    async def __aenter__(self: "ClaudeSession") -> "ClaudeSession":
        return self

    async def __aexit__(self: "ClaudeSession", *args: Any) -> None:
        pass

    async def query(self: "ClaudeSession", prompt: str) -> Response:
        """Stub query method."""
        return Response("")


__all__ = ["ClaudeSession", "SessionOptions"]
