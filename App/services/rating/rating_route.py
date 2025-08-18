# rating_route.py
from fastapi import APIRouter, Body
from .rating_schema import DealInput
from .rating import call_groq_audit
import json

router = APIRouter(prefix="/rating", tags=["Rating"])

@router.post("/")
def audit_deal(input_data: DealInput = Body(...)):
    """Audit the provided deal JSON and return the score + results. Provide the resullt in a descriptive way"""
    result_json_str = call_groq_audit({
    "text": input_data.text,
    "form_fields": [f.dict() for f in input_data.form_fields]
})


    try:
        result = json.loads(result_json_str)
    except Exception:
        return {"error": "Failed to parse AI response", "raw_response": result_json_str}

    return result
