"""Script to run Celery worker."""

import subprocess
import sys
from pathlib import Path

if __name__ == "__main__":
    # Use subprocess to call celery directly
    # This is more reliable than trying to use Celery's programmatic API
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    cmd = [
        sys.executable,
        "-m",
        "celery",
        "-A",
        "agentic_clinical_assistant.workers.celery_app",
        "worker",
        "--loglevel=info",
        "--queues=default,agent,ingestion,evaluation,benchmark",
    ]
    
    subprocess.run(cmd, cwd=project_root)
