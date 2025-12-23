"""Tools API routes."""

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, status

from agentic_clinical_assistant.tools.registry import get_registry

router = APIRouter(prefix="/tools", tags=["tools"])


@router.get("")
async def list_tools() -> Dict[str, Any]:
    """
    List all available tools.

    Returns:
        Dictionary with all registered tools
    """
    registry = get_registry()
    tools = registry.list_tools()

    # Format for API response
    tools_list = []
    for name, tool_def in tools.items():
        tools_list.append({
            "name": name,
            "description": tool_def["description"],
            "parameters": tool_def["parameters"],
        })

    return {
        "tools": tools_list,
        "count": len(tools_list),
    }


@router.get("/{tool_name}")
async def get_tool_info(tool_name: str) -> Dict[str, Any]:
    """
    Get information about a specific tool.

    Args:
        tool_name: Name of the tool

    Returns:
        Tool definition
    """
    registry = get_registry()
    tool = registry.get_tool(tool_name)

    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool '{tool_name}' not found",
        )

    return {
        "name": tool["name"],
        "description": tool["description"],
        "parameters": tool["parameters"],
    }


@router.post("/{tool_name}/execute")
async def execute_tool(tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a tool.

    Args:
        tool_name: Name of the tool
        parameters: Tool parameters

    Returns:
        Tool execution result
    """
    registry = get_registry()
    tool = registry.get_tool(tool_name)

    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool '{tool_name}' not found",
        )

    try:
        # Execute tool using registry
        result = await registry.execute_tool(tool_name, **parameters)

        return {
            "tool": tool_name,
            "result": result,
            "status": "success",
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Tool execution failed: {str(e)}",
        )

