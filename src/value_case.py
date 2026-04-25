import anthropic
import argparse
import json
import os
import re
import sys
from datetime import datetime
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(__file__))
from value_prompts import build_analyst_prompt, build_builder_prompt

load_dotenv()


def run_analyst(brief_content: str, product: str = None) -> dict:
    client = anthropic.Anthropic()
    system, user = build_analyst_prompt(brief_content, product=product)

    print("\nStep 1: Analysing brief...")

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system=system,
        messages=[{"role": "user", "content": user}]
    )

    raw = response.content[0].text.strip()
    raw = re.sub(r'^```(?:json)?\s*', '', raw)
    raw = re.sub(r'\s*```$', '', raw)

    return json.loads(raw)


def run_builder(analyst_output: dict, context: str = None) -> str:
    client = anthropic.Anthropic()
    system, user = build_builder_prompt(analyst_output, context=context)

    print("Step 2: Building value case...")

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=system,
        messages=[{"role": "user", "content": user}]
    )

    return response.content[0].text


def save_value_case(company: str, content: str) -> str:
    date_str = datetime.now().strftime("%d-%b-%Y").lower()
    clean_name = company.strip('"\'').lower().replace(' ', '-')
    filename = f"value_case_{clean_name}_{date_str}.md"
    output_path = os.path.join(os.path.dirname(__file__), "..", filename)
    output_path = os.path.normpath(output_path)

    with open(output_path, "w") as f:
        f.write(f"# Value Case: {company}\n")
        f.write(f"*Generated: {datetime.now().strftime('%d %b %Y')}*\n\n")
        f.write(content)
    return output_path


def resolve_brief_path(brief_arg: str) -> str:
    if os.path.exists(brief_arg):
        return brief_arg
    project_root = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
    candidate = os.path.join(project_root, brief_arg)
    if os.path.exists(candidate):
        return candidate
    return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Value Intelligence — Value Case Builder")
    parser.add_argument("brief", help="Path to a Phase 1 research brief (.md file)")
    parser.add_argument("--product", help='Specific product being sold e.g. "Celonis process mining"', default=None)
    parser.add_argument("--context", help='Deal context e.g. "CFO-led cost reduction initiative"', default=None)
    args = parser.parse_args()

    brief_path = resolve_brief_path(args.brief)
    if not brief_path:
        print(f"Error: Brief file not found: {args.brief}")
        sys.exit(1)

    with open(brief_path, "r") as f:
        brief_content = f.read()

    try:
        analyst_output = run_analyst(brief_content, product=args.product)
    except json.JSONDecodeError as e:
        print(f"Error: Analyst step did not return valid JSON: {e}")
        sys.exit(1)

    company = analyst_output.get("company", "unknown")
    mode = analyst_output.get("mode", "consulting")
    pain_count = len(analyst_output.get("pain_points", []))
    print(f"  Mode: {mode} | Company: {company} | Pain points: {pain_count}")

    value_case = run_builder(analyst_output, context=args.context)

    path = save_value_case(company, value_case)
    print(f"\nValue case saved to: {path}")
    print("\n" + "=" * 60 + "\n")
    print(value_case)
