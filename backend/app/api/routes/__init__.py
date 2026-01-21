from fastapi import APIRouter

from app.api.routes.health import router as health_router
from app.api.routes.tasks import router as tasks_router
from app.api.routes.chat import router as chat_router
from app.api.routes.chatkit import router as chatkit_router

router = APIRouter()

# Include route modules
router.include_router(health_router)
router.include_router(tasks_router)
router.include_router(chat_router)
router.include_router(chatkit_router)
