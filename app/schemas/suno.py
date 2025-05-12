from pydantic import BaseModel, Field
from typing import List, Optional

class SubmitGenSongReq(BaseModel):
    prompt: str
    mv: Optional[str] = None
    title: Optional[str] = None
    tags: Optional[str] = None
    gpt_description_prompt: Optional[str] = Field(None, alias="gpt_description_prompt")
    task_id: Optional[str] = Field(None, alias="task_id")
    continue_at: Optional[float] = Field(None, alias="continue_at")
    continue_clip_id: Optional[str] = Field(None, alias="continue_clip_id")
    make_instrumental: bool = Field(False, alias="make_instrumental")

class SubmitGenLyricsReq(BaseModel):
    prompt: str

class FetchReq(BaseModel):
    ids: List[str]
    action: str