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
        "vehicle_overview": get_field(
            'vehicle_overview',
            'Vehicle overview information is missing. Please include details about the make, model, year, mileage, condition, and key features of the vehicle.'
        ),
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

        "apr_bonus_rule": get_field(
            'apr_bonus_rule',
            'APR data not found. Ensure APR is competitive (6.5–9.5% typical). If too high, negotiate a rate reduction or explore outside financing. Minimum 200 words.'),

        "lease_audit": get_field(
            'lease_audit',
            ' For the lease audit section, if the deal is a lease, do check the details of the lease terms including residual value, money factor, lease duration, monthly payments, and implications for the buyers financial risk and benefits.'
        ),
        "negotiation_insight": get_field(
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
    try:
        # Call AI with just the input data
        result_json_str = call_groq_audit({
            "text": input_data.text,
            "form_fields": [f.dict() for f in input_data.form_fields]
        })

        # Parse AI response
        result = json.loads(result_json_str)
        
        # Validate required fields exist (updated for new flag structure)
        required_fields = ['score', 'buyer_name', 'dealer_name', 'badge', 'buyer_message', 'red_flags', 'green_flags', 
                          'blue_flags', 'normalized_pricing', 'apr', 'term', 
                          'quote_type', 'bundle_abuse', 'narrative']
        
        for field in required_fields:
            if field not in result:
                if field in ['buyer_name', 'dealer_name']:
                    result[field] = None
                else:
                    raise ValueError(f"Missing required field: {field}")

        # Format narrative
        formatted_narrative_text = format_narrative(
            narrative_data=result.get("narrative", {}),
            normalized_pricing=result.get("normalized_pricing", {})
        )

        # Return structured response with fallbacks
        return {
            "score": result.get("score", 0),
            "buyer_name": result.get("buyer_name"),  # From AI analysis
            "dealer_name": result.get("dealer_name"),
            "badge": result.get("badge", "Unknown"),
            "buyer_message": result.get("buyer_message", "No message generated"),
            "red_flags": result.get("red_flags", []),
            "green_flags": result.get("green_flags", []),
            "blue_flags": result.get("blue_flags", []),
            "normalized_pricing": result.get("normalized_pricing", {}),
            "apr": result.get("apr", {}),
            "term": result.get("term", {}),
            "quote_type": result.get("quote_type", "Unknown"),
            "bundle_abuse": result.get("bundle_abuse", {}),
            "narrative": {
                "formatted": formatted_narrative_text
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
