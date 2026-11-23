from dataclasses import dataclass
from collections.abc import Awaitable, Callable


@dataclass
class ToolContext:
    role: str
    delegates: dict[str, str]
    spawn: Callable[[str, str], Awaitable[str]]