from fastapi import APIRouter, Body
from .rating_schema import DealInput
from .rating import call_groq_audit
import json

router = APIRouter(prefix="/rating", tags=["Rating"])


def format_narrative(narrative_data, normalized_pricing=None):
    def get_field(key, fallback):
        value = narrative_data.get(key)
        return value if value and str(value).strip().lower() != "none" else fallback

    return {
        "trust_score_summary": get_field(
            'trust_score_summary',
            'No trust score summary provided. Please include insights on fairness, transparency, and APR context. Minimum 200 words.'
        ),
        "market_comparison": get_field(
            'market_comparison',
            'No market comparison found. Include pricing comparisons for GAP, VSC, and total deal structure. Minimum 200 words.'
        ),
        "gap_logic": get_field(
            'gap_logic',
            'GAP pricing information is missing. However, GAP can be beneficial for buyers with high loan-to-value ratios, low down payments, or long-term loans. Assess buyer risk and discuss coverage value.'
        ),
        "vsc_logic": get_field(
            'vsc_logic',
            'VSC price data is unavailable. Still, extended warranties may be useful for buyers planning to keep the car long-term or purchasing a vehicle with uncertain reliability.'
        ),
        "lease_audit": get_field(
            'lease_audit',
            'For the lease audit section, if the deal is a lease, provide a detailed, 200+ word analysis of the lease terms including residual value, money factor, lease duration, monthly payments, and implications for the buyers financial risk and benefits. If this is not a lease, state so briefly.'
        ),
        "apr_bonus_rule": get_field(
            'apr_bonus_rule',
            'APR data not found. Ensure APR is competitive (6.5–9.5% typical). If too high, negotiate a rate reduction or explore outside financing. Minimum 200 words.'
        ),
        "negotiation_insights": get_field(
            'negotiation_insight',
            '''- **Ask to waive unnecessary fees**  
Use third-party deal comparisons to justify fair pricing.

- **Negotiate APR and monthly payments**  
Reduce long-term costs and improve affordability.

- **Request added perks**  
Push for free service, accessories, or better warranty coverage.'''
        ),
        "final_recommendation": get_field(
            'final_recommendation',
            'Final recommendation is missing. Please provide a concise summary of key findings and next steps for the buyer. Minimum 200 words.'
        )
    }


@router.post("/")
def audit_deal(input_data: DealInput = Body(...)):
    """
    Audit the provided deal JSON and return the score + results.
    The narrative will be returned in both raw and formatted form.
    EACH SECTION MUST CONTAIN MORE THAN 200 WORDS.
    """

    # Step 1: Compose AI instruction for reasoning-rich output
    ai_instruction = """
You are a deal rating assistant. Your task is to evaluate an auto financing or lease deal, based on buyer-provided data. Your output must include well-reasoned, financial, and contextual analysis.

Each of the following sections must be returned in a `narrative.raw` object. If any data is missing (such as GAP or VSC prices), still provide a generalized recommendation based on best practices, risk factors, and financing context.

You MUST return your response in this exact JSON format:

{
  "narrative": {
    "raw": {
      "trust_score_summary": "...",
      "market_comparison": "...",
      "gap_logic": "...",
      "vsc_logic": "...",
      "lease_audit": "...",
      "apr_bonus_rule": "...",
      "negotiation_insight": "...",
      "final_recommendation": "..."
    }
  },
  "score": ...,
  "badge": "...",
  "buyer_message": "...",
  "flags": [...],
  "bonuses": [...],
  "advisories": [...],
  "normalized_pricing": {...},
  "apr": {...},
  "term": {...},
  "quote_type": "...",
  "bundle_flag": {...}
}

If any data is missing (like GAP or VSC prices), still give generalized, reasonable financial advice using logic and buyer risk. Each `narrative.raw` section must be >200 words and demonstrate human reasoning.

Return only valid JSON. Do not include extra commentary or markdown. No bullet points unless in `negotiation_insight`.

Use your own financial logic. Do not rely on strict price thresholds. Always provide reasoning based on deal context. If there is not sufficient data, provide a generalized answer. Do not tell the data is missing.
"""

    # Step 2: Call AI with instruction and input data
    result_json_str = call_groq_audit({
    "system_instruction": ai_instruction.strip(),
    "input": {
        "text": input_data.text,
        "form_fields": [f.dict() for f in input_data.form_fields]
    }
})



    # Step 3: Parse AI response
    try:
        result = json.loads(result_json_str)
    except Exception:
        return {
            "error": "❌ Failed to parse AI response",
            "raw_response": result_json_str
        }

    # Optional debug logging
    print("DEBUG - Raw Narrative Output:\n", json.dumps(result.get("narrative", {}), indent=2))

    # Step 4: Format narrative using fallback-friendly logic
    formatted_narrative_text = format_narrative(
        narrative_data=result.get("narrative", {}).get("raw", {}),
        normalized_pricing=result.get("normalized_pricing", {})
    )

    # Step 5: Return structured response
    return {
    "score": result.get("score"),
    "badge": result.get("badge"),
    "buyer_message": result.get("buyer_message"),
    "flags": result.get("flags"),
    "bonuses": result.get("bonuses"),
    "advisories": result.get("advisories"),
    "normalized_pricing": result.get("normalized_pricing"),
    "apr": result.get("apr"),
    "term": result.get("term"),
    "quote_type": result.get("quote_type"),
    "bundle_flag": result.get("bundle_flag"),
    "narrative": {
        "raw": result.get("narrative", {}).get("raw", {})
    }
}

