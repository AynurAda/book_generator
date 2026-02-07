"""
Test Gemini Deep Research API - gauge cost and quality.
"""

import os
import time
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("ERROR: GEMINI_API_KEY not set")
    exit(1)

from google import genai

client = genai.Client(api_key=api_key)

# ============================================================================
# TEST QUERIES - Conceptually focused, open-ended
# In production, these would be generated dynamically from book vision
# ============================================================================

QUERIES = {
    "theoretical_advances": """
What new theoretical frameworks, methods, or paradigms have emerged in Neuro-symbolic AI (2024-2025)?

For each significant advance:
- What is the core idea or insight?
- What problem does it solve that previous approaches couldn't?
- How does it work conceptually?
- What are the key papers that introduced it?

I'm writing an educational book - I need to UNDERSTAND and EXPLAIN these ideas, not just list them.
""",

    "reasoning_methods": """
What advances have been made in neural theorem proving and formal reasoning (2024-2025)?

- What new approaches combine learning with logical inference?
- How are systems achieving mathematical reasoning?
- What theoretical insights explain why these methods work?
- What are the key techniques and how do they differ?

Explain the methods deeply enough that I can teach them to ML researchers.
""",

    "knowledge_integration": """
How are neural networks being integrated with structured knowledge (2024-2025)?

- What methods exist for combining neural models with knowledge graphs, ontologies, or logical rules?
- How do these approaches handle the neural-symbolic interface?
- What are the tradeoffs between different integration strategies?
- What theoretical foundations underpin these approaches?

Focus on HOW things work and WHY, not just what exists.
""",

    "learning_reasoning_unification": """
What progress has been made toward unifying learning and reasoning (2024-2025)?

- How are gradient-based learning and symbolic inference being combined?
- What approaches make logic differentiable?
- How is probabilistic reasoning integrated with neural networks?
- What are the key unsolved challenges?

I need conceptual depth to write chapters that give readers true understanding.
""",
}


def run_deep_research(query: str, query_name: str) -> dict:
    """Run a deep research query and return results."""

    print(f"\n{'='*60}")
    print(f"QUERY: {query_name}")
    print(f"{'='*60}")
    print(f"Started: {datetime.now().strftime('%H:%M:%S')}")

    start_time = time.time()

    try:
        interaction = client.interactions.create(
            input=query,
            agent='deep-research-pro-preview-12-2025',
            background=True,
        )

        print(f"Job ID: {interaction.id}")

        # Poll for completion
        while True:
            interaction = client.interactions.get(interaction.id)
            elapsed = time.time() - start_time
            print(f"  Status: {interaction.status} ({elapsed:.0f}s)", end='\r')

            if interaction.status == "completed":
                print(f"\n✓ Completed in {elapsed:.1f}s")
                break
            elif interaction.status == "failed":
                print(f"\n✗ Failed: {getattr(interaction, 'error', 'Unknown')}")
                return {"error": str(getattr(interaction, 'error', 'Unknown')), "query_name": query_name}

            time.sleep(10)

            if elapsed > 1800:  # 30 min timeout
                return {"error": "Timeout", "query_name": query_name}

        # Extract results
        output = ""
        if hasattr(interaction, 'outputs') and interaction.outputs:
            output = interaction.outputs[-1].text

        return {
            "query_name": query_name,
            "elapsed_seconds": time.time() - start_time,
            "output": output,
            "output_chars": len(output),
            "estimated_tokens": len(output) // 4,
        }

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e), "query_name": query_name}


def estimate_cost(results: list[dict]) -> dict:
    """Estimate cost based on Gemini 3 Pro pricing."""
    # Input: $2/1M, Output: $12/1M
    # Deep Research has intermediate reasoning tokens (~5x output estimate)

    total_output_tokens = sum(r.get("estimated_tokens", 0) for r in results if "error" not in r)
    total_with_intermediate = total_output_tokens * 6  # output + 5x intermediate
    input_tokens = len(results) * 500  # ~500 tokens per query

    input_cost = (input_tokens / 1_000_000) * 2.00
    output_cost = (total_with_intermediate / 1_000_000) * 12.00

    return {
        "queries_run": len([r for r in results if "error" not in r]),
        "total_output_tokens": total_output_tokens,
        "estimated_with_intermediate": total_with_intermediate,
        "estimated_cost": f"${input_cost + output_cost:.2f}",
    }


def main():
    import sys

    # Allow selecting which queries to run
    if len(sys.argv) > 1:
        selected = sys.argv[1:]
        queries_to_run = {k: v for k, v in QUERIES.items() if k in selected}
    else:
        queries_to_run = QUERIES

    print("="*60)
    print("GEMINI DEEP RESEARCH TEST")
    print("="*60)
    print(f"Queries to run: {list(queries_to_run.keys())}")
    print(f"Estimated cost: ~${3 * len(queries_to_run)}-${5 * len(queries_to_run)}")
    print("="*60)

    results = []

    for name, query in queries_to_run.items():
        result = run_deep_research(query, name)
        results.append(result)

        # Save after each query in case of interruption
        with open("deep_research_results.json", "w") as f:
            json.dump({"results": results, "timestamp": datetime.now().isoformat()}, f, indent=2)

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    for r in results:
        if "error" in r:
            print(f"  {r['query_name']}: FAILED - {r['error']}")
        else:
            print(f"  {r['query_name']}: {r['output_chars']} chars, {r['elapsed_seconds']:.0f}s")

    cost = estimate_cost(results)
    print(f"\nEstimated total cost: {cost['estimated_cost']}")
    print(f"Results saved to: deep_research_results.json")

    # Print outputs
    for r in results:
        if "output" in r:
            print(f"\n{'='*60}")
            print(f"OUTPUT: {r['query_name']}")
            print(f"{'='*60}\n")
            print(r["output"][:8000] if len(r["output"]) > 8000 else r["output"])
            if len(r["output"]) > 8000:
                print(f"\n... [{len(r['output']) - 8000} more chars, see JSON file]")


if __name__ == "__main__":
    main()
