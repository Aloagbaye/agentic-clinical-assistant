"""Workflow mode tools for structured outputs."""

import json
import re
from typing import Any, Dict, List, Optional


async def build_checklist(
    answer_text: str,
    format: str = "json",
) -> Dict[str, Any]:
    """
    Build structured checklist from procedure answer.

    Args:
        answer_text: Answer text containing procedure steps
        format: Output format (json, markdown, html)

    Returns:
        Dictionary with checklist in requested format
    """
    # Extract steps from answer
    steps = _extract_procedure_steps(answer_text)

    # Build checklist structure
    checklist = {
        "title": "Procedure Checklist",
        "steps": [
            {
                "id": i + 1,
                "description": step,
                "completed": False,
                "notes": "",
            }
            for i, step in enumerate(steps)
        ],
        "total_steps": len(steps),
    }

    # Format output
    if format == "json":
        return {"checklist": checklist, "format": "json"}
    elif format == "markdown":
        markdown = _checklist_to_markdown(checklist)
        return {"checklist": markdown, "format": "markdown"}
    elif format == "html":
        html = _checklist_to_html(checklist)
        return {"checklist": html, "format": "html"}
    else:
        return {"checklist": checklist, "format": "json"}


def _extract_procedure_steps(text: str) -> List[str]:
    """Extract procedure steps from text."""
    steps = []

    # Pattern 1: Numbered steps (1., 2., etc.)
    numbered_pattern = r"(?:^|\n)\s*(\d+)[\.\)]\s+(.+?)(?=\n\s*\d+[\.\)]|\n\n|$)"
    matches = re.findall(numbered_pattern, text, re.MULTILINE)
    if matches:
        steps = [match[1].strip() for match in matches]
        return steps

    # Pattern 2: Bullet points (-, *, •)
    bullet_pattern = r"(?:^|\n)\s*[-*•]\s+(.+?)(?=\n\s*[-*•]|\n\n|$)"
    matches = re.findall(bullet_pattern, text, re.MULTILINE)
    if matches:
        steps = [match.strip() for match in matches]
        return steps

    # Pattern 3: "Step X:" format
    step_pattern = r"(?:^|\n)\s*[Ss]tep\s+\d+[:\-]\s+(.+?)(?=\n\s*[Ss]tep|\n\n|$)"
    matches = re.findall(step_pattern, text, re.MULTILINE)
    if matches:
        steps = [match.strip() for match in matches]
        return steps

    # Fallback: Split by sentences if no structure found
    if not steps:
        sentences = re.split(r"[.!?]\s+", text)
        steps = [s.strip() for s in sentences if len(s.strip()) > 20][:10]  # Limit to 10 steps

    return steps


def _checklist_to_markdown(checklist: Dict[str, Any]) -> str:
    """Convert checklist to Markdown format."""
    lines = [f"# {checklist['title']}\n"]
    for step in checklist["steps"]:
        checkbox = "- [ ]" if not step["completed"] else "- [x]"
        lines.append(f"{checkbox} {step['id']}. {step['description']}")
    return "\n".join(lines)


def _checklist_to_html(checklist: Dict[str, Any]) -> str:
    """Convert checklist to HTML format."""
    html = f"<h1>{checklist['title']}</h1>\n<ul>\n"
    for step in checklist["steps"]:
        checked = "checked" if step["completed"] else ""
        html += f'  <li><input type="checkbox" {checked}> {step["id"]}. {step["description"]}</li>\n'
    html += "</ul>"
    return html


async def extract_workflow_actions(
    answer_text: str,
    format: str = "json",
) -> Dict[str, Any]:
    """
    Extract workflow actions from answer.

    Args:
        answer_text: Answer text containing workflow steps
        format: Output format (json, markdown, html)

    Returns:
        Dictionary with workflow actions in requested format
    """
    steps = _extract_procedure_steps(answer_text)

    actions = {
        "workflow_name": "Procedure Workflow",
        "actions": [
            {
                "id": i + 1,
                "action": step,
                "type": "step",
                "dependencies": [],
            }
            for i, step in enumerate(steps)
        ],
        "total_actions": len(steps),
    }

    # Format output
    if format == "json":
        return {"workflow": actions, "format": "json"}
    elif format == "markdown":
        markdown = _workflow_to_markdown(actions)
        return {"workflow": markdown, "format": "markdown"}
    elif format == "html":
        html = _workflow_to_html(actions)
        return {"workflow": html, "format": "html"}
    else:
        return {"workflow": actions, "format": "json"}


def _workflow_to_markdown(workflow: Dict[str, Any]) -> str:
    """Convert workflow to Markdown format."""
    lines = [f"# {workflow['workflow_name']}\n"]
    for action in workflow["actions"]:
        lines.append(f"## Action {action['id']}: {action['action']}")
        if action.get("dependencies"):
            lines.append(f"Dependencies: {', '.join(action['dependencies'])}")
    return "\n".join(lines)


def _workflow_to_html(workflow: Dict[str, Any]) -> str:
    """Convert workflow to HTML format."""
    html = f"<h1>{workflow['workflow_name']}</h1>\n<ol>\n"
    for action in workflow["actions"]:
        html += f'  <li><strong>{action["action"]}</strong></li>\n'
    html += "</ol>"
    return html

