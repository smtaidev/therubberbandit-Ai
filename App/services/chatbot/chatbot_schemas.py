from pydantic import BaseModel, Field
from typing import List, Optional


class ChatRequest(BaseModel):
    message: str
    audit_flags: Optional[List[str]] = []
    context: Optional[str] = None
class ChatResponse(BaseModel):
    reply: str