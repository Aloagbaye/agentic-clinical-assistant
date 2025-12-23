"""Script to run Celery beat (scheduler)."""

import subprocess
import sys
from pathlib import Path

if __name__ == "__main__":
    # Use subprocess to call celery beat directly
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    cmd = [
        sys.executable,
        "-m",
        "celery",
        "-A",
        "agentic_clinical_assistant.workers.celery_app",
        "beat",
        "--loglevel=info",
    ]
    
    subprocess.run(cmd, cwd=project_root)
