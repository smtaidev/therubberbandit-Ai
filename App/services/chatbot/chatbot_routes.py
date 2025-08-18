import os, httpx
from cachetools import LRUCache
from typing import List
from fastapi import APIRouter, HTTPException, Query
from App.services.chatbot.chatbot_schemas import ChatRequest, ChatResponse
from App.core.config import settings
router = APIRouter(prefix="/concierge", tags=["concierge"])

MAX_THREADS = 10000
memory: LRUCache[str, List[dict]] = LRUCache(maxsize=MAX_THREADS)

@router.post("", response_model=ChatResponse)
async def concierge(
    req: ChatRequest,
    thread_id: str = Query(..., description="unique conversation id")
):
    api_key = settings.GROQ_API_KEY
    if not api_key:
        raise HTTPException(500, "GROQ_API_KEY not set")

    # Build dynamic system prompt based on audit flags
    base = (
        "You are an expert car-deal negotiator called 'Concierge'.\n"
        "The dealer target price is $100.\n"
    )
    if "GAP_HIGH" in req.audit_flags:
        base += "- Dealer GAP price is flagged as excessive; insist on fair market.\n"
    if "VSC_HIGH" in req.audit_flags:
        base += "- VSC add-on is overpriced; push for reduction.\n"
    base += (
        "Be firm but professional. "
        "Return only the concise counter-offer or acceptance the buyer should send."
    )

    # Server-side memory
    history = memory.get(thread_id, [])
    if not history:
        history = [{"role": "system", "content": base}]
    history.append({"role": "user", "content": req.message})

    payload = {
        "model": settings.GROQ_MODEL,
        "messages": history,
        "max_tokens": 80,
        "temperature": 0.55
    }

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            r = await client.post(
                settings.GROQ_URL,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json=payload
            )
            r.raise_for_status()
            reply = r.json()["choices"][0]["message"]["content"].strip()

            # Save assistant turn
            history.append({"role": "assistant", "content": reply})
            memory[thread_id] = history
            return ChatResponse(reply=reply)
        except Exception as e:
            raise HTTPException(502, f"Groq error: {e}")