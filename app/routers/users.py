import logging
from fastapi import APIRouter

router = APIRouter()
logger = logging.getLogger("naija-soul")


@router.get("/users/{user_id}/reviews")
async def get_user_reviews(user_id: str):
    return {
        "user_id": user_id,
        "message": "Memories are stored in-memory and reset on server restart. "
                   "Use the user_id returned from /simulate-review or /recommend "
                   "responses for session-scoped tracking. "
                   "Pass it back as user_id in subsequent requests.",
    }
