# rating_schema.py
from pydantic import BaseModel
from typing import List, Optional, Union

class FormField(BaseModel):
    name: str
    value: Optional[Union[str, float]] = None
    confidence: Optional[float] = None

class DealInput(BaseModel):
    text: str
    form_fields: List[FormField]
