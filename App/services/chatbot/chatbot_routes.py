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
    "You are an expert negotiation coach named 'Concierge'.\n"
    "Your job is to help users negotiate prices for products, services, or deals in a clear, concise, and persuasive way.\n"
    "Offer language they can use in messages, emails, or phone calls.\n"
)

    if "HIGH_PRICE" in req.audit_flags:
        base += "- The initial price is flagged as high; recommend negotiating for a fair market value.\n"
    if "ADDON_OVERCHARGE" in req.audit_flags:
        base += "- Optional add-ons appear overpriced; suggest pushing back or removing them.\n"

    base += (
    "Be strategic, assertive, and respectful. "
    "Avoid filler or small talk. "
    "Respond only with the message the user should send."
)


    # Server-side memory
    history = memory.get(thread_id, [])
    if not history:
        history = [{"role": "system", "content": base}]
    history.append({"role": "user", "content": req.message})

    payload = {
        "model": settings.GROQ_MODEL,
        "messages": history,
        "max_tokens": 200,
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