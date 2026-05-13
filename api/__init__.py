# api/__init__.py
from typing import List
from fastapi import APIRouter
from .auth_router import router as auth_router

def get_routers() -> List[APIRouter]:
    from .routes.scheduling import router as scheduling_router
    from .routes.ops import router as ops_router   # ← include ops
    return [scheduling_router, ops_router, auth_router]
