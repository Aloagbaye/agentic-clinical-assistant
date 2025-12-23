"""Tool registry for managing available tools."""

from typing import Any, Callable, Dict, Optional

from agentic_clinical_assistant.tools.core import (
    generate_answer,
    redact_phi,
    retrieve_evidence,
    run_backend_benchmark,
    verify_grounding,
)
from agentic_clinical_assistant.tools.workflow import build_checklist, extract_workflow_actions


class ToolRegistry:
    """Registry for managing available tools."""

    def __init__(self):
        """Initialize tool registry."""
        self._tools: Dict[str, Dict[str, Any]] = {}
        self._register_default_tools()

    def _register_default_tools(self) -> None:
        """Register default tools."""
        self.register(
            name="retrieve_evidence",
            function=retrieve_evidence,
            description="Retrieve evidence from vector databases",
            parameters={
                "query": {"type": "string", "required": True, "description": "Search query"},
                "backend": {"type": "string", "required": False, "description": "Vector backend to use"},
                "filters": {"type": "object", "required": False, "description": "Metadata filters"},
                "top_k": {"type": "integer", "required": False, "description": "Number of results", "default": 10},
            },
        )

        self.register(
            name="redact_phi",
            function=redact_phi,
            description="Redact PHI/PII from text",
            parameters={
                "text": {"type": "string", "required": True, "description": "Text to redact"},
                "aggressive": {"type": "boolean", "required": False, "description": "Use aggressive redaction", "default": False},
            },
        )

        self.register(
            name="run_backend_benchmark",
            function=run_backend_benchmark,
            description="Run benchmark evaluation on vector backends",
            parameters={
                "eval_set_id": {"type": "string", "required": True, "description": "Evaluation dataset ID"},
                "backends": {"type": "array", "required": False, "description": "Backends to evaluate"},
                "benchmark_id": {"type": "string", "required": False, "description": "Benchmark run ID"},
            },
        )

        self.register(
            name="generate_answer",
            function=generate_answer,
            description="Generate answer from evidence",
            parameters={
                "evidence_bundle": {"type": "array", "required": True, "description": "Evidence items"},
                "request_text": {"type": "string", "required": True, "description": "User request"},
                "prompt_version": {"type": "string", "required": False, "description": "Prompt version"},
                "model": {"type": "string", "required": False, "description": "LLM model"},
            },
        )

        self.register(
            name="verify_grounding",
            function=verify_grounding,
            description="Verify grounding of answer in evidence",
            parameters={
                "draft_answer": {"type": "string", "required": True, "description": "Draft answer"},
                "evidence_bundle": {"type": "array", "required": True, "description": "Evidence items"},
            },
        )

        self.register(
            name="build_checklist",
            function=build_checklist,
            description="Build structured checklist from procedure answer",
            parameters={
                "answer_text": {"type": "string", "required": True, "description": "Answer text"},
                "format": {"type": "string", "required": False, "description": "Output format (json/markdown/html)", "default": "json"},
            },
        )

        self.register(
            name="extract_workflow_actions",
            function=extract_workflow_actions,
            description="Extract workflow actions from answer",
            parameters={
                "answer_text": {"type": "string", "required": True, "description": "Answer text"},
                "format": {"type": "string", "required": False, "description": "Output format (json/markdown/html)", "default": "json"},
            },
        )

    def register(
        self,
        name: str,
        function: Callable,
        description: str,
        parameters: Dict[str, Any],
    ) -> None:
        """
        Register a tool.

        Args:
            name: Tool name
            function: Tool function
            description: Tool description
            parameters: Tool parameters schema
        """
        self._tools[name] = {
            "name": name,
            "function": function,
            "description": description,
            "parameters": parameters,
        }

    def get_tool(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get tool by name.

        Args:
            name: Tool name

        Returns:
            Tool definition or None
        """
        return self._tools.get(name)

    def list_tools(self) -> Dict[str, Dict[str, Any]]:
        """
        List all registered tools.

        Returns:
            Dictionary of all tools
        """
        return self._tools.copy()

    async def execute_tool(self, name: str, **kwargs: Any) -> Any:
        """
        Execute a tool.

        Args:
            name: Tool name
            **kwargs: Tool arguments

        Returns:
            Tool result
        """
        import asyncio
        
        tool = self.get_tool(name)
        if not tool:
            raise ValueError(f"Tool '{name}' not found")

        func = tool["function"]
        if asyncio.iscoroutinefunction(func):
            return await func(**kwargs)
        else:
            return func(**kwargs)


# Global registry instance
_registry: Optional[ToolRegistry] = None


def get_registry() -> ToolRegistry:
    """Get global tool registry instance."""
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry

