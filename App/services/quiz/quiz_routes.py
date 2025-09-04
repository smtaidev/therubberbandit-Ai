import httpx
from fastapi import APIRouter, HTTPException, Query
from App.services.quiz.quiz_schemas import QuizQuestion
from App.core.config import settings
from typing import List

router = APIRouter(prefix="/quiz", tags=["quiz"])

QUIZ_GENERATION_PROMPT = (
    "You are an expert car sales trainer. Generate a multiple choice quiz question "
    "to test consumer knowledge about car buying, dealership practices, financing, trade-ins, or warranties. "
    "Output in JSON with the following keys: "
    "`question` (string), `options` (list of 4 strings), `correct_answer` (one of the options), "
    "`explanation` (string explaining why it's correct)."
)

@router.post("/generate", response_model=List[QuizQuestion])
async def generate_quiz_questions(
    count: int = Query(1, ge=1, le=10, description="Number of quiz questions to generate")
):
    if not settings.GROQ_API_KEY or not settings.GR_URL:
        raise HTTPException(status_code=500, detail="LLM API settings not configured")

    # Create chat messages
    messages = [{"role": "system", "content": QUIZ_GENERATION_PROMPT}]
    messages.append({"role": "user", "content": f"Generate {count} unique quiz question(s). Return only a JSON list."})

    payload = {
        "model": settings.GROQ_MODEL,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 1000
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                settings.GROQ_URL,
                headers={
                    "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                    "Content-Type": "application/json"
                },
                json=payload
            )
            response.raise_for_status()
            raw_output = response.json()["choices"][0]["message"]["content"]

        # Evaluate the returned JSON
        import json
        questions = json.loads(raw_output)

        return [QuizQuestion(**q) for q in questions]

    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Quiz generation failed: {e}")
