from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict

class Message(BaseModel):
    role: str
    content: str
    name: Optional[str] = None

class FunctionSpec(BaseModel):
    name: str
    description: Optional[str]
    parameters: Dict[str, Any]

class ToolSpec(BaseModel):
    id: Optional[str]
    type: str
    function: FunctionSpec

class GeneralOpenAIRequest(BaseModel):
    model: Optional[str]
    # Use default_factory to avoid mutable default argument
    messages: Optional[List[Message]] = Field(default_factory=list)
    stream: Optional[bool] = False
    max_tokens: Optional[int] = Field(None, alias="max_tokens")
    temperature: Optional[float]
    top_p: Optional[float]
    top_k: Optional[int] = Field(None, alias="top_k")
    function_call: Optional[Any] = Field(None, alias="function_call")
    frequency_penalty: Optional[float] = Field(None, alias="frequency_penalty")
    presence_penalty: Optional[float] = Field(None, alias="presence_penalty")
    tool_choice: Optional[str] = Field(None, alias="tool_choice")
    tools: Optional[List[ToolSpec]] = None

    class Config:
        allow_population_by_field_name = True