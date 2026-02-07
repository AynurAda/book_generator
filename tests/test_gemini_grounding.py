"""Test Gemini grounded search API using official SDK."""

import os
from dotenv import load_dotenv

from google import genai
from google.genai import types

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("ERROR: GEMINI_API_KEY not set")
    exit(1)

client = genai.Client(api_key=api_key)

# Test claim to verify
test_claim = "The Transformer architecture was introduced in the paper 'Attention Is All You Need' by Vaswani et al. in 2017."

prompt = f"""You are a rigorous fact-checker. Verify this claim with ORIGINAL/PRIMARY sources.

CLAIM TO VERIFY:
"{test_claim}"

CONTEXT: This claim is from a book about machine learning.

YOUR TASK:
1. Use Google Search to find the ORIGINAL source
2. Determine if the claim is DIRECTLY supported by evidence
3. Be STRICT - only verify if you find explicit support

RESPOND IN THIS EXACT JSON FORMAT:
{{
    "verified": true/false,
    "confidence": 0.0-1.0,
    "source_url": "URL of the ORIGINAL/PRIMARY source (empty if not verified)",
    "source_title": "Title of the original source",
    "authors": "Original author names",
    "year": "Original publication year",
    "supporting_quote": "Exact quote or close paraphrase from the ORIGINAL source",
    "explanation": "Brief explanation including why this is the original source"
}}

ONLY output valid JSON, nothing else."""

# Configure grounding
grounding_tool = types.Tool(
    google_search=types.GoogleSearch()
)

config = types.GenerateContentConfig(
    tools=[grounding_tool],
    temperature=1.0,
    max_output_tokens=4096,
    response_mime_type="application/json",
)

print(f"Testing Gemini with Google Search grounding...")
print(f"Claim: {test_claim}")
print("-" * 50)

try:
    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=prompt,
        config=config,
    )

    print("\n=== RESPONSE TEXT ===")
    print(response.text)

    # Check for grounding metadata
    if hasattr(response, 'candidates') and response.candidates:
        candidate = response.candidates[0]
        if hasattr(candidate, 'grounding_metadata') and candidate.grounding_metadata:
            print("\n=== GROUNDING METADATA ===")
            gm = candidate.grounding_metadata
            if hasattr(gm, 'grounding_chunks'):
                for i, chunk in enumerate(gm.grounding_chunks[:3]):
                    if hasattr(chunk, 'web') and chunk.web:
                        print(f"  [{i+1}] {getattr(chunk.web, 'title', 'N/A')}")
                        print(f"      URL: {getattr(chunk.web, 'uri', 'N/A')}")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
