from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)          # latest dealer reply
    audit_flags: list[str] = Field(default_factory=list)  # GAP/VSC/etc flags

class ChatResponse(BaseModel):
    reply: str