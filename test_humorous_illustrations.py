#!/usr/bin/env python3
"""
Test script for generating humorous illustrations using Gemini.

Tests different prompts to see how well Gemini can create
educational-yet-humorous illustrations for the book.
"""

import os
import io
import asyncio
import logging
from datetime import datetime

from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test prompts - humorous takes on neuro-symbolic AI concepts
TEST_PROMPTS = [
    {
        "concept": "Symbolic AI vs Neural Networks",
        "prompt": "A nerdy robot wearing glasses and reading a rulebook (labeled 'LOGIC') having a heated debate with a brain made of tangled Christmas lights. The robot is pointing at a flowchart while the brain just vibes. Clean illustration style, educational humor.",
    },
    {
        "concept": "The AI Winter",
        "prompt": "A sad robot sitting alone in a snowy landscape, holding a sign that says 'Will reason for funding'. Abandoned computers covered in snow in the background. Melancholic but humorous, editorial cartoon style.",
    },
    {
        "concept": "Combinatorial Explosion",
        "prompt": "A tiny computer sweating profusely while looking at an impossibly large tree of branching paths that extends into infinity. The tree branches are literally exploding with small 'BOOM' effects. Whimsical technical illustration.",
    },
    {
        "concept": "Knowledge Graphs",
        "prompt": "A librarian owl wearing a monocle, carefully connecting different books with red string like a conspiracy board, but it's actually making perfect sense. Clean vector illustration style.",
    },
    {
        "concept": "The Black Box Problem",
        "prompt": "A scientist peering into a mysterious black box with question marks floating around their head. Inside the box (visible to viewer), a tiny wizard is performing magic. Educational illustration with a touch of humor.",
    },
    {
        "concept": "Gradient Descent",
        "prompt": "A ball character with a determined face rolling down a hilly landscape, passing signs that say 'LOSS: HIGH' at the top and 'LOSS: LOW' at the bottom. Some valleys have treasure chests (global minimum) while others have fake gold (local minima). Playful educational style.",
    },
    {
        "concept": "Attention Mechanism",
        "prompt": "A classroom scene where a teacher (transformer) has spotlights for eyes, shining bright beams on the most important students while others sit in shadow. The illuminated students look smugly important. Clean illustration style.",
    },
    {
        "concept": "Logic Tensor Networks",
        "prompt": "A robot and a philosopher sitting at a cafe, sharing a drink called 'Fuzzy Logic Latte'. The robot is showing the philosopher a tensor on its tablet while the philosopher shows back a scroll of logical formulas. They're finding common ground. Warm, friendly illustration.",
    },
    {
        "concept": "Backpropagation of Blame",
        "prompt": "A line of cartoon neurons pointing fingers at each other in a chain, with the last one pointing at the input saying 'It was YOUR fault!'. Error values floating above each connection. Humorous technical diagram style.",
    },
    {
        "concept": "Overfitting",
        "prompt": "A neural network character that has memorized a phone book and looks very proud, but when asked a simple question looks completely confused. The phone book is labeled 'Training Data'. Exaggerated cartoon style.",
    },
    {
        "concept": "The Frame Problem",
        "prompt": "A robot trying to make a sandwich but frozen in existential crisis because it's calculating whether making the sandwich will affect the position of the moon. Galaxies swirl in its thought bubble while a simple sandwich sits unfinished. Absurdist humor illustration.",
    },
    {
        "concept": "Differentiable Programming",
        "prompt": "Traditional code blocks and mathematical derivatives holding hands and walking into a sunset together, with a rainbow overhead labeled 'Gradients Flow Here'. Sweet and slightly cheesy, clean vector art.",
    },
    {
        "concept": "Causal Reasoning",
        "prompt": "A detective owl examining a crime scene of spilled coffee, with arrows connecting 'elbow bump' to 'cup falls' to 'coffee spills' to 'keyboard ruined'. Correlation (a suspicious-looking statistics chart) is being escorted away in handcuffs. Mystery/noir style with humor.",
    },
    {
        "concept": "The Symbol Grounding Problem",
        "prompt": "A confused robot holding the word 'APPLE' in one hand and a real apple in the other, with question marks connecting them. The robot is surrounded by floating words that aren't attached to anything. Clean educational illustration.",
    },
    {
        "concept": "Neuro-Symbolic Integration",
        "prompt": "A neural network (depicted as a glowing brain) and a logic engine (depicted as a clockwork mechanism) doing a fusion dance like in Dragon Ball Z, with the resulting fusion being a powerful hybrid creature made of both gears and neurons. Dynamic, energetic illustration style.",
    },
    # === WITTY ADDITIONS ===
    {
        "concept": "Curse of Dimensionality",
        "prompt": "A tiny explorer with a flashlight standing at the entrance of a corridor that splits into thousands of identical doors, each door leading to more doors. The explorer's supplies are labeled 'Sample Size: 100'. A sign reads 'Welcome to 10,000 Dimensions'. Existential dread meets technical accuracy.",
    },
    {
        "concept": "Regularization",
        "prompt": "An overweight neural network at a gym, with a stern personal trainer (labeled 'L2') forcing it to drop its excess weights. Some weights are crying as they fall off. A sign on the wall says 'No Overfitting Zone'. Clean cartoon style.",
    },
    {
        "concept": "Vanishing Gradients",
        "prompt": "A game of telephone between neurons in a deep network. The first neuron shouts a clear number, but by the last neuron it's become an inaudible whisper approaching zero. The deep neurons look starved and confused. Vintage illustration style.",
    },
    {
        "concept": "Emergent Behavior",
        "prompt": "Simple ants, each following a tiny rule card, accidentally creating the Mona Lisa on the ground through their collective movement. None of them realize what they've made. One ant says 'I just follow the gradient'. Whimsical scientific illustration.",
    },
    {
        "concept": "Turing Test",
        "prompt": "A masquerade ball where humans wear robot masks and robots wear human masks. Everyone is suspicious of everyone. A judge in the corner is sweating, unable to tell anyone apart. Elegant but absurd.",
    },
    {
        "concept": "P vs NP",
        "prompt": "Split scene: Left side shows someone instantly checking a completed Sudoku with a satisfied smile. Right side shows the same person aged 50 years, surrounded by crumpled papers, still trying to solve it. Caption potential: 'Verification vs Discovery'. Clean editorial style.",
    },
    {
        "concept": "Occam's Razor",
        "prompt": "A barber shop where a philosophical barber is shaving away elaborate, overcomplicated explanations from theories. On the floor lie discarded hypotheses labeled 'unnecessary assumptions'. The simplest explanation sits smugly in the chair, looking clean. Victorian illustration style.",
    },
    {
        "concept": "No Free Lunch Theorem",
        "prompt": "A cafeteria where different algorithms sit at tables. Each plate costs different amounts for different algorithms - what's free for one is expensive for another. A 'Universal Algorithm' sits alone with an infinitely long bill. Diner aesthetic.",
    },
    {
        "concept": "Inductive Bias",
        "prompt": "A neural network wearing tinted glasses, seeing the world through its assumptions. Different networks with different colored glasses see the same data completely differently. One insists the dress is blue, another gold. Clean modern illustration.",
    },
    {
        "concept": "Mode Collapse",
        "prompt": "A GAN art gallery where every painting is the exact same face, and the discriminator is enthusiastically approving each one while the curator weeps. The generator looks proud but confused. Satirical art world style.",
    },
    # === PHILOSOPHICAL ===
    {
        "concept": "Chinese Room",
        "prompt": "A person inside a room, mechanically matching Chinese symbols using a giant rulebook, passing perfect responses through a slot. Outside, people marvel at the 'intelligence'. Inside, the person has no idea what any of it means. Their eyes are empty but their hands are precise. Thoughtful, slightly unsettling illustration.",
    },
    {
        "concept": "Ship of Theseus Neural Network",
        "prompt": "A neural network where each neuron is being replaced one by one with new neurons. The original neurons watch from a retirement home labeled 'Deprecated Weights'. A philosopher asks: 'Is it still the same model?' Contemplative style.",
    },
    {
        "concept": "Plato's Cave of Machine Learning",
        "prompt": "Neural networks chained in a cave, watching shadows of data on the wall (projected from real-world objects behind them). One network has broken free and sees actual reality - high-dimensional, terrifying, beautiful. Classical philosophy meets tech.",
    },
    {
        "concept": "The Map is Not the Territory",
        "prompt": "A model holding a beautiful, detailed map of reality, but the map is subtly wrong - rivers flow uphill, cities are misplaced. The model confidently navigates using only the map, about to walk off a cliff that isn't on the map. Tragicomic illustration.",
    },
    {
        "concept": "Qualia - What Mary Didn't Know",
        "prompt": "A colorblind robot scientist who knows everything about color wavelengths, physics of light, and human perception, finally seeing red for the first time. The robot's face shows something new - something the equations never captured. Poignant, minimal style.",
    },
    {
        "concept": "Determinism and Free Will",
        "prompt": "A robot at a crossroads, sweating over a decision, while above it a giant hand holds puppet strings that lead to a deterministic universe of cause and effect. The robot thinks it's choosing. Is it? Philosophical noir style.",
    },
    {
        "concept": "Gödel's Incompleteness",
        "prompt": "A formal system (depicted as a perfect crystalline structure) with a crack running through it - a statement that says 'This statement cannot be proven within this system'. The system is trying to prove itself complete, but the crack keeps growing. Abstract mathematical aesthetic.",
    },
    {
        "concept": "The Hard Problem of Consciousness",
        "prompt": "A neuroscientist has perfectly mapped every neuron and connection in a brain, displayed on a massive board. But floating above the board is an ineffable glow labeled '???' that the map cannot capture. The scientist reaches for it but their hand passes through. Mysterious, contemplative.",
    },
    {
        "concept": "Simulation Hypothesis",
        "prompt": "A neural network training smaller neural networks, which train even smaller ones, infinite regression like mirrors facing each other. At some level, tiny researchers are studying their 'universe' unaware they're weights in a larger model. Escher-like recursive illustration.",
    },
    {
        "concept": "The Bitter Lesson",
        "prompt": "A graveyard of clever hand-crafted AI systems with elaborate tombstones ('Expert Systems', 'Hand-coded Features', 'Symbolic Reasoning'). In the distance, a simple but massive neural network grows ever larger, fed only by compute and data. It casts a long shadow. Bittersweet editorial cartoon.",
    },
]


async def generate_test_images(output_dir: str, model_name: str = "gemini-3-pro-image-preview"):
    """Generate test images for all prompts."""
    os.makedirs(output_dir, exist_ok=True)

    # Initialize the client
    client = genai.Client()

    results = []

    for i, item in enumerate(TEST_PROMPTS, 1):
        concept = item["concept"]
        prompt = item["prompt"]

        logger.info(f"\n[{i}/{len(TEST_PROMPTS)}] Generating: {concept}")
        logger.info(f"Prompt: {prompt[:80]}...")

        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE", "TEXT"]
                )
            )

            # Extract image from response
            image_saved = False
            for part in response.candidates[0].content.parts:
                if part.inline_data is not None:
                    safe_name = concept.lower().replace(" ", "_").replace("/", "_")[:30]
                    filename = f"{i:02d}_{safe_name}.png"
                    filepath = os.path.join(output_dir, filename)

                    image_data = part.inline_data.data
                    image = Image.open(io.BytesIO(image_data))
                    image.save(filepath)

                    logger.info(f"  Saved: {filename}")
                    results.append({"concept": concept, "status": "success", "file": filename})
                    image_saved = True
                    break

            if not image_saved:
                # Check if there's text response
                text_parts = [p.text for p in response.candidates[0].content.parts if hasattr(p, 'text') and p.text]
                if text_parts:
                    logger.warning(f"  No image, got text: {text_parts[0][:100]}...")
                else:
                    logger.warning(f"  No image in response")
                results.append({"concept": concept, "status": "no_image", "file": None})

        except Exception as e:
            logger.error(f"  Failed: {e}")
            results.append({"concept": concept, "status": "error", "error": str(e)})

    # Print summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    success = sum(1 for r in results if r["status"] == "success")
    print(f"Generated: {success}/{len(TEST_PROMPTS)} images")
    print(f"Output directory: {output_dir}")

    if success < len(TEST_PROMPTS):
        print("\nFailed/Skipped:")
        for r in results:
            if r["status"] != "success":
                print(f"  - {r['concept']}: {r.get('error', r['status'])}")

    return results


def main():
    """Main entry point."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"output/test_illustrations_{timestamp}"

    print("="*60)
    print("HUMOROUS ILLUSTRATION TEST")
    print("="*60)
    print(f"Testing {len(TEST_PROMPTS)} prompts")
    print(f"Output: {output_dir}")
    print("="*60 + "\n")

    asyncio.run(generate_test_images(output_dir))


if __name__ == "__main__":
    main()
