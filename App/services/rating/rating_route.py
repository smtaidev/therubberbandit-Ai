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
            'On trust_score_summary, provide 500+ word analysis ',
            'No trust score summary provided. Please include insights on fairness, transparency, and APR context. Minimum 200 words.'
        ),
        "market_comparison": get_field(
            'On market_comparison , provide 500+ word analysis',
            'No market comparison found. Include pricing comparisons for GAP, VSC, and total deal structure. Minimum 200 words.'
        ),
        "gap_logic": get_field(
            'On gap_logic, , provide 500+ word analysis',
            'GAP pricing information is missing. However, GAP can be beneficial for buyers with high loan-to-value ratios, low down payments, or long-term loans. Assess buyer risk and discuss coverage value.'
        ),
        "vsc_logic": get_field(
            'On vsc_logic , provide 500+ word analysis',
            'VSC price data is unavailable. Still, extended warranties may be useful for buyers planning to keep the car long-term or purchasing a vehicle with uncertain reliability.'
        ),
        "lease_audit": get_field(
            'On lease_audit, provide 500+ word analysis',
            'For the lease audit section, if the deal is a lease, provide a detailed, 500+ word analysis of the lease terms including residual value, money factor, lease duration, monthly payments, and implications for the buyers financial risk and benefits. If this is not a lease, state so briefly.'
        ),
        "apr_bonus_rule": get_field(
            'On apr_bonus_rule, , provide 500+ word analysis',
            'APR data not found. Ensure APR is competitive (6.5–9.5% typical). If too high, negotiate a rate reduction or explore outside financing. Minimum 200 words.'
        ),
        "negotiation_insights": get_field(
            'negotiation_insight, provide 500+ word analysis',
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
    # ... (keep your existing format_narrative function and initial setup)

    try:
        # Call AI with just the input data (no system instruction in user message)
        result_json_str = call_groq_audit({
            "text": input_data.text,
            "form_fields": [f.dict() for f in input_data.form_fields]
        })

        # Parse AI response
        result = json.loads(result_json_str)
        
        # Validate required fields exist
        required_fields = ['score', 'badge', 'buyer_message', 'flags', 'bonuses', 
                          'advisories', 'normalized_pricing', 'apr', 'term', 
                          'quote_type', 'bundle_flag', 'narrative']
        
        for field in required_fields:
            if field not in result:
                raise ValueError(f"Missing required field: {field}")

        # Format narrative
        formatted_narrative_text = format_narrative(
            narrative_data=result.get("narrative", {}).get("raw", {}),
            normalized_pricing=result.get("normalized_pricing", {})
        )

        # Return structured response with fallbacks
        return {
            "score": result.get("score", 0),
            "badge": result.get("badge", "Unknown"),
            "buyer_message": result.get("buyer_message", "No message generated"),
            "flags": result.get("flags", []),
            "bonuses": result.get("bonuses", []),
            "advisories": result.get("advisories", []),
            "normalized_pricing": result.get("normalized_pricing", {}),
            "apr": result.get("apr", {}),
            "term": result.get("term", {}),
            "quote_type": result.get("quote_type", "Unknown"),
            "bundle_flag": result.get("bundle_flag", {}),
            "narrative": {
                "formatted": formatted_narrative_text,
                "raw": result.get("narrative", {}).get("raw", {})
            }
        }

    except json.JSONDecodeError:
        return {
            "error": "❌ Failed to parse AI response as JSON",
            "raw_response": result_json_str
        }
    except ValueError as e:
        return {
            "error": f"❌ Invalid response format: {str(e)}",
            "raw_response": result_json_str
        }
    except Exception as e:
        return {
            "error": f"❌ Unexpected error: {str(e)}",
            "raw_response": result_json_str if 'result_json_str' in locals() else None
        }