# api/state.py
from __future__ import annotations
from typing import Any, Dict

# Global conversation/session storage
SESSION_STORE: Dict[str, Dict[str, Any]] = {}