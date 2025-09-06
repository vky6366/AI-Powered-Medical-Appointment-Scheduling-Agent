from .routes.scheduling import router as scheduling_router
from .routes.ops import router as ops_router

def get_routers():
    return [scheduling_router, ops_router]
