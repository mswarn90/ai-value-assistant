import json


def build_analyst_prompt(brief_content: str, product: str = None) -> tuple[str, str]:
    if product:
        mode_instruction = f"""You are evaluating fit between a specific product and this company's pain points.
Product: {product}

For each pain point:
- Ground it in specific evidence from the brief
- Map how {product} addresses it — be honest about fit strength (strong / moderate / stretch)
- If fit is a stretch, say so. A credible value case never oversells."""
        mode_value = "product"
    else:
        mode_instruction = """You are acting as an independent consultant with no product allegiance.

For each pain point:
- Ground it in specific evidence from the brief
- Envision the capability or approach that would resolve it
- Suggest 1-2 specific products or vendors that could deliver that capability"""
        mode_value = "consulting"

    schema = {
        "company": "company name extracted from the brief",
        "mode": mode_value,
        "product": product if product else None,
        "pain_points": [
            {
                "name": "short name for this pain point",
                "description": "1-2 sentence description grounded in the brief",
                "evidence": "direct quote or specific signal from the brief",
                "value_type": "cost reduction | revenue growth | risk reduction | efficiency gain",
                "solution_vision": "what capability or approach resolves this",
                "product_angle": "product mode: how the named product maps to this pain. consulting mode: specific product/vendor suggestions",
                "fit_strength": "strong | moderate | stretch | n/a"
            }
        ]
    }

    system = f"""You are a senior Value Engineering analyst. Your job is to read a research brief and identify the 2-3 highest-potential pain points for a business value case.

{mode_instruction}

Output ONLY valid JSON with no preamble, commentary, or markdown formatting. Match this exact structure:

{json.dumps(schema, indent=2)}"""

    user = f"""Analyse this research brief and identify the 2-3 highest-potential pain points.

{brief_content}"""

    return system, user


def build_builder_prompt(analyst_output: dict, context: str = None) -> tuple[str, str]:
    company = analyst_output.get("company", "the company")
    product = analyst_output.get("product")
    pain_points = analyst_output.get("pain_points", [])

    context_line = f"\nDeal context: {context}" if context else ""
    product_line = f"\nProduct: {product}" if product else ""

    system = """You are a senior Value Engineer writing a value case for an enterprise AI engagement.

Your output must be a structured markdown document that a CFO can read in 5 minutes and engage with seriously.

Rules:
- For modeled $ figures, write the number cleanly with (modeled) after it — e.g. $150M–$350M (modeled)
- For benchmarked % figures, cite the source inline — e.g. 40%–60% [Workiva, 2024]
- Use ranges, not false precision — $2M–$4M is more credible than $3.2M
- Write like a practitioner, not a consultant template — specific, grounded, no filler
- Never use: leverage, utilize, holistic, seamless, robust, cutting-edge, comprehensive

Output exactly these sections in order:

## Value Hypothesis
One sentence. Pattern: [Company] can [achieve outcome] by [mechanism], [qualifier].

## Value Drivers
*(Figures modeled — to be refined with client data)*

One subsection per pain point. For each:

### [Driver Name]
- **Pain:** what the company is experiencing today, specifically
- **Current state:** baseline description with assumed figures where needed
- **Target state:** improved state description
- **Improvement:** X%–Y% [Source, Year]
- **Estimated impact:** $X–$Y (modeled)
- **Solution:** how the identified product or approach addresses this

## ROI Skeleton *(Indicative)*
| Metric | Year 1 | Year 2 | Year 3 |
|---|---|---|---|
| Investment | $X–$Y (modeled) | $X–$Y (modeled) | $X–$Y (modeled) |
| Benefits | $X–$Y (modeled) | $X–$Y (modeled) | $X–$Y (modeled) |
| Net value | $X–$Y (modeled) | $X–$Y (modeled) | $X–$Y (modeled) |

**Payback period:** X–Y months (modeled)
**3-year ROI:** Xx–Xx (modeled)

**Key assumptions:**
List 3-4 explicit assumptions the model rests on.

## Executive Narrative
2-3 paragraphs for the economic buyer. Specific, grounded in their situation, forward-looking without speculating."""

    user = f"""Build a value case using the analyst findings below.

Company: {company}{product_line}{context_line}

Analyst findings:
{json.dumps(pain_points, indent=2)}"""

    return system, user
