"""
Claim planning for subsections.

This module generates explicit claim plans BEFORE content generation.
The LLM plans what factual claims it will make, then we verify those,
then content generation is strictly constrained to verified claims only.

This ensures NO unverified factual claims can appear in the final text.
"""

import logging
from typing import List, Dict, Optional
import asyncio

import synalinks

from .models import Claim

logger = logging.getLogger(__name__)


class PlannedClaim(synalinks.DataModel):
    """A single planned factual claim."""
    claim_text: str = synalinks.Field(
        description="The specific factual claim to be made (precise and verifiable)"
    )
    claim_type: str = synalinks.Field(
        description="Type: statistic, research_finding, definition, attribution, historical, technical"
    )
    importance: str = synalinks.Field(
        description="critical (essential to the point), high (key supporting fact), medium (helpful), low (optional)"
    )
    why_needed: str = synalinks.Field(
        description="Brief explanation of why this claim is needed for the subsection"
    )


class SubsectionClaimPlan(synalinks.DataModel):
    """Plan of all factual claims for a subsection."""
    subsection_summary: str = synalinks.Field(
        description="Brief summary of what this subsection will cover"
    )
    planned_claims: list[PlannedClaim] = synalinks.Field(
        description="List of all factual claims planned for this subsection"
    )
    conceptual_points: list[str] = synalinks.Field(
        description="Non-factual points (explanations, examples, reasoning) that don't need citations"
    )


class SubsectionClaimPlanInput(synalinks.DataModel):
    """Input for planning claims for a subsection."""
    topic: str = synalinks.Field(description="Book topic")
    goal: str = synalinks.Field(description="Book goal")
    audience: str = synalinks.Field(description="Target audience")
    chapter_name: str = synalinks.Field(description="Chapter name")
    section_name: str = synalinks.Field(description="Section name")
    subsection_name: str = synalinks.Field(description="Subsection name")
    section_plan: str = synalinks.Field(description="The section plan context")
    book_plan: str = synalinks.Field(description="High-level book plan")


async def plan_subsection_claims(
    topic: str,
    goal: str,
    audience: str,
    chapter_name: str,
    section_name: str,
    subsection_name: str,
    section_plan: str,
    book_plan: str,
    language_model,
) -> SubsectionClaimPlan:
    """
    Plan all factual claims for a single subsection.

    The LLM explicitly lists what facts it plans to state,
    so we can verify them BEFORE content generation.
    """
    planner = synalinks.Generator(
        data_model=SubsectionClaimPlan,
        language_model=language_model,
        temperature=1.0,
        instructions="""You are planning the FACTUAL CONTENT for a book subsection.

Your task: List ALL factual claims you would need to make when writing this subsection.

A FACTUAL CLAIM is any statement that:
- States a specific fact that could be true or false
- Would require a citation in an academic book
- Is NOT just explanation, reasoning, or conceptual discussion

EXAMPLES OF FACTUAL CLAIMS:
- "Transformers were introduced by Vaswani et al. in 2017"
- "BERT achieves 93.2% accuracy on SQuAD"
- "The attention mechanism has O(n²) complexity"
- "GPT-3 has 175 billion parameters"
- "Knowledge graphs store information as subject-predicate-object triples"

EXAMPLES OF NON-FACTUAL CONTENT (no citation needed):
- "To understand attention, imagine you're reading a sentence..."
- "This approach works because..."
- "One way to think about this is..."
- "For example, suppose we have a neural network that..."

BE COMPREHENSIVE: List EVERY fact you might state. It's better to list too many claims than too few.
Missing a claim means it cannot appear in the final text.

BE SPECIFIC: "Studies show X works well" is too vague.
Instead: "Smith et al. (2023) demonstrated X achieves Y% improvement on Z benchmark"

For each claim, indicate:
- claim_type: statistic, research_finding, definition, attribution, historical, technical
- importance: critical (the subsection fails without it), high (key point), medium (supporting), low (nice detail)
- why_needed: brief explanation of why this claim matters for the subsection"""
    )

    input_data = SubsectionClaimPlanInput(
        topic=topic,
        goal=goal,
        audience=audience,
        chapter_name=chapter_name,
        section_name=section_name,
        subsection_name=subsection_name,
        section_plan=section_plan,
        book_plan=book_plan,
    )

    result = await planner(input_data)
    return result


def convert_planned_claims_to_claims(
    plan: SubsectionClaimPlan,
    chapter_name: str,
    section_name: str,
    subsection_name: str,
) -> List[Claim]:
    """Convert planned claims to Claim objects for verification."""
    claims = []
    plan_dict = plan.get_json()

    for i, planned in enumerate(plan_dict.get("planned_claims", [])):
        # Handle both dict and object access
        if isinstance(planned, dict):
            claim_text = planned.get("claim_text", "")
            claim_type = planned.get("claim_type", "technical")
            importance = planned.get("importance", "medium")
        else:
            claim_text = getattr(planned, "claim_text", "")
            claim_type = getattr(planned, "claim_type", "technical")
            importance = getattr(planned, "importance", "medium")

        if not claim_text:
            continue

        claim = Claim(
            id=f"{chapter_name[:10]}_{section_name[:10]}_{subsection_name[:10]}_{i}".replace(" ", "_"),
            content=claim_text,
            chapter=chapter_name,
            section=section_name,
            subsection=subsection_name,
            claim_type=claim_type,
            importance=importance,
        )
        claims.append(claim)

    return claims


async def plan_all_subsection_claims(
    topic_data: dict,
    hierarchy: Dict[str, Dict[str, List[str]]],
    book_plan: str,
    section_plans: Dict[str, dict],
    language_model,
    max_concurrent: int = 10,
) -> tuple[Dict[str, SubsectionClaimPlan], List[Claim]]:
    """
    Plan claims for ALL subsections in the book.

    Args:
        topic_data: Book topic, goal, audience
        hierarchy: {chapter: {section: [subsections]}}
        book_plan: Formatted book plan
        section_plans: {chapter: {section_plans: [...]}}
        language_model: Synalinks language model
        max_concurrent: Max concurrent planning tasks

    Returns:
        Tuple of:
        - Dict mapping "chapter::section::subsection" to SubsectionClaimPlan
        - List of all Claim objects for verification
    """
    all_plans = {}
    all_claims = []

    # Build list of all subsections to plan
    tasks_to_run = []
    for chapter_name, sections in hierarchy.items():
        chapter_section_plans = section_plans.get(chapter_name, {}).get("section_plans", [])

        for section_idx, (section_name, subsections) in enumerate(sections.items()):
            # Get section plan text
            section_plan_text = ""
            if section_idx < len(chapter_section_plans):
                sp = chapter_section_plans[section_idx]
                if isinstance(sp, dict):
                    section_plan_text = sp.get("section_summary", "") + "\n" + sp.get("key_points", "")

            for subsection_name in subsections:
                tasks_to_run.append({
                    "chapter": chapter_name,
                    "section": section_name,
                    "subsection": subsection_name,
                    "section_plan": section_plan_text,
                })

    total = len(tasks_to_run)
    logger.info(f"Planning claims for {total} subsections...")

    semaphore = asyncio.Semaphore(max_concurrent)

    async def plan_one(task_info: dict, idx: int):
        async with semaphore:
            logger.info(f"Planning claims [{idx+1}/{total}]: {task_info['subsection'][:40]}...")

            try:
                plan = await plan_subsection_claims(
                    topic=topic_data["topic"],
                    goal=topic_data["goal"],
                    audience=topic_data.get("audience", "technical readers"),
                    chapter_name=task_info["chapter"],
                    section_name=task_info["section"],
                    subsection_name=task_info["subsection"],
                    section_plan=task_info["section_plan"],
                    book_plan=book_plan,
                    language_model=language_model,
                )

                # Convert to claims
                claims = convert_planned_claims_to_claims(
                    plan,
                    task_info["chapter"],
                    task_info["section"],
                    task_info["subsection"],
                )

                key = f"{task_info['chapter']}::{task_info['section']}::{task_info['subsection']}"
                return key, plan, claims

            except Exception as e:
                logger.error(f"Failed to plan claims for {task_info['subsection']}: {e}")
                return None, None, []

    # Run all planning tasks
    results = await asyncio.gather(*[
        plan_one(task, i) for i, task in enumerate(tasks_to_run)
    ])

    for key, plan, claims in results:
        if key and plan:
            all_plans[key] = plan
            all_claims.extend(claims)

    # Summary
    logger.info(f"Claim planning complete:")
    logger.info(f"  - Subsections planned: {len(all_plans)}")
    logger.info(f"  - Total claims: {len(all_claims)}")

    # Breakdown by importance
    critical = sum(1 for c in all_claims if c.importance == "critical")
    high = sum(1 for c in all_claims if c.importance == "high")
    medium = sum(1 for c in all_claims if c.importance == "medium")
    low = sum(1 for c in all_claims if c.importance == "low")
    logger.info(f"  - By importance: {critical} critical, {high} high, {medium} medium, {low} low")

    return all_plans, all_claims
