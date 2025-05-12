"""
Router for Suno endpoints: submit, fetch, account.
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Any, Dict, List

from app.utils.auth import verify_secret_token
from app.schemas.suno import SubmitGenSongReq, SubmitGenLyricsReq, FetchReq
from app.services.suno_service import suno_service

router = APIRouter(
    prefix="",
    dependencies=[Depends(verify_secret_token)],
    responses={401: {"description": "Unauthorized"}},
)

def build_response(data: Any) -> Dict[str, Any]:
    return {"code": "success", "message": "", "data": data}

@router.post("/submit/music")
async def submit_music(req: SubmitGenSongReq):
    """Submit a song generation task using Suno."""
    task_id = suno_service.submit_song(req.dict(exclude_none=True))
    return build_response(task_id)

@router.post("/submit/lyrics")
async def submit_lyrics(req: SubmitGenLyricsReq):
    """Submit a lyrics generation task using Suno."""
    task_id = suno_service.submit_lyrics(req.dict(exclude_none=True))
    return build_response(task_id)

@router.get("/fetch/{task_id}")
async def fetch_by_id(task_id: str):
    try:
        result = suno_service.fetch_by_id(task_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return build_response(result)

@router.post("/fetch")
async def fetch_many(req: FetchReq):
    tasks = suno_service.fetch_tasks(req.ids, req.action)
    return build_response(tasks)

@router.get("/account")
async def get_account():
    info = suno_service.get_account_info()
    return build_response(info)