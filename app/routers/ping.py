from fastapi import APIRouter

router = APIRouter()

@router.get("/ping")
async def ping():
    """
    Health check endpoint, returns a pong message.
    """
    return {"message": "pong"}