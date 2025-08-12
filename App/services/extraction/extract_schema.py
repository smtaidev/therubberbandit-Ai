from pydantic import BaseModel
from typing import List, Optional

class FormField(BaseModel):
    name: str
    value: str
    confidence: float

class ExtractResponse(BaseModel):
    text: str
    form_fields: Optional[List[FormField]] = []
