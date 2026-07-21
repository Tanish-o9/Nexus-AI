from __future__ import annotations

import json
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, ValidationError

from app.tools.schemas import ToolContext, ToolError, ToolResult

ToolHandler = Callable[[BaseModel, ToolContext], Awaitable[ToolResult]]


@dataclass(frozen=True)
class RegisteredTool:
    name: str
    description: str
    input_model: type[BaseModel]
    handler: ToolHandler

    def definition(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.input_model.model_json_schema(),
            },
        }


class ToolRegistry:
    """The sole allow-list and validation boundary for agent tool calls."""

    def __init__(self) -> None:
        self._tools: dict[str, RegisteredTool] = {}

    def register(self, tool: RegisteredTool) -> None:
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' is already registered.")
        self._tools[tool.name] = tool

    def definitions(self) -> list[dict[str, Any]]:
        return [tool.definition() for tool in self._tools.values()]

    async def execute(
        self, name: str, arguments: dict[str, Any] | str | None, context: ToolContext
    ) -> ToolResult:
        tool = self._tools.get(name)
        if tool is None:
            return self._error(name, "unknown_tool", "This tool is not available to the executor.")

        try:
            parsed_arguments = json.loads(arguments) if isinstance(arguments, str) else arguments or {}
            payload = tool.input_model.model_validate(parsed_arguments)
        except (ValidationError, json.JSONDecodeError) as exc:
            return self._error(name, "invalid_arguments", str(exc))

        try:
            return await tool.handler(payload, context)
        except Exception:
            # Avoid leaking provider credentials or implementation details to the model.
            return self._error(
                name,
                "tool_unavailable",
                "The tool is temporarily unavailable. Continue without it or explain the limitation.",
                retryable=True,
            )

    @staticmethod
    def _error(name: str, code: str, message: str, retryable: bool = False) -> ToolResult:
        return ToolResult(
            tool_name=name,
            ok=False,
            error=ToolError(code=code, message=message, retryable=retryable),
        )


tool_registry = ToolRegistry()
