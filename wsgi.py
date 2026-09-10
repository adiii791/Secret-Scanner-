"""WSGI entry point — used by gunicorn and AWS Elastic Beanstalk."""
import sys
from pathlib import Path

# Make backend/ importable regardless of working directory.
_backend = Path(__file__).resolve().parent / "backend"
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from app import app  # noqa: E402

__all__ = ["app"]
