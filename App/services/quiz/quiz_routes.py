import httpx
from fastapi import APIRouter, HTTPException, Query
from App.services.quiz.quiz_schemas import QuizQuestion
from App.core.config import settings
from typing import List
import json 
from enum import Enum

router = APIRouter(prefix="/quiz", tags=["quiz"])

class SupportedLanguage(str, Enum):
    english = "English"
    spanish = "Spanish"
    arabic  = "Arabic"
    mandarin = "Mandarin"
    hindi = "Hindi"
     

QUIZ_GENERATION_PROMPT = """
You are an expert car sales trainer. Generate multiple-choice quiz questions to test consumer knowledge about car buying, dealership practices, financing, trade-ins, GAP Logic, VSC Logic, Lease Audit, APR or warranties.
MAKE SURE YOU PROVIDE THE ANSWERS CORRECTLY.

Respond only with a valid JSON array. Do not use markdown formatting like ```json.

Each object in the array should have the following structure:
- question: A string representing the quiz question.
- options: An object with keys "A", "B", "C", and "D", and values being the corresponding answer texts.
- correct_answer: One of the keys "A", "B", "C", or "D", corresponding to the correct option.
- explanation: A short string explaining why the correct answer is correct.

The entire output should be in the language requested by the user.
Example format:

[
  {
    "question": "What is the purpose of a vehicle history report when buying a used car?",
    "options": {
      "A": "To determine the car's fuel efficiency",
      "B": "To check for past accidents and title issues",
      "C": "To find out the original price of the car",
      "D": "To estimate the car's future resale value"
    },
    "correct_answer": "B",
    "explanation": "A vehicle history report provides important information about a used car, including any past accidents, title issues, service history, and whether the car has been reported as stolen."
  }
]
"""





@router.post("/generate", response_model=List[QuizQuestion])
async def generate_quiz_questions(
    count: int = Query(1, ge=1, le=10),
    language: SupportedLanguage = Query(SupportedLanguage.english)
):
    if not settings.GROQ_API_KEY or not settings.GROQ_URL:
        raise HTTPException(status_code=500, detail="LLM API settings not configured")

    # Create chat messages
    messages = [{"role": "system", "content": QUIZ_GENERATION_PROMPT}]
    messages.append({
    "role": "user",
    "content": f"Generate {count} unique quiz question(s) in {language.value}. Return only a JSON list."
})


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

            parsed = response.json()
            raw_output = parsed["choices"][0]["message"]["content"]

            # 👇 Clean triple-backtick markdown if present
            cleaned = raw_output.strip().strip("`").strip()
            if cleaned.startswith("json"):
                cleaned = cleaned[len("json"):].strip()

            # 👇 Parse the JSON
            data = json.loads(cleaned)

            # 👇 Ensure it's a list even if one question is returned
            if isinstance(data, dict):
                data = [data]

            return [QuizQuestion(**q) for q in data]

    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Quiz generation failed: {e}")
