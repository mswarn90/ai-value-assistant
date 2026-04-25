import anthropic
import argparse
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(__file__))
from prompts import build_system_prompt
from tools import SEARCH_TOOL, run_search

load_dotenv()


def run_research(company: str, industry: str, focus: str = None) -> str:
    client = anthropic.Anthropic()
    system_prompt = build_system_prompt(focus=focus)

    focus_note = f" | Focus: {focus}" if focus else ""
    user_message = f"Research {company} in the {industry} industry and produce a structured research brief.{focus_note}"

    messages = [{"role": "user", "content": user_message}]

    print(f"\nResearching {company} ({industry}){focus_note}...")

    while True:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=[
                {
                    "type": "text",
                    "text": system_prompt,
                    "cache_control": {"type": "ephemeral"}
                }
            ],
            tools=[SEARCH_TOOL],
            messages=messages
        )

        if response.stop_reason == "end_turn":
            for block in response.content:
                if hasattr(block, "text"):
                    return block.text
            break

        if response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    days = block.input.get("days")
                    days_note = f" (last {days} days)" if days else ""
                    print(f"  Searching{days_note}: {block.input['query']}")
                    result = run_search(block.input["query"], days=days)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result
                    })
            messages.append({"role": "user", "content": tool_results})

    return ""


def save_brief(company: str, industry: str, brief: str, focus: str = None) -> str:
    date_str = datetime.now().strftime("%d-%b-%Y").lower()
    clean_name = company.strip('"\'').lower().replace(' ', '-')
    focus_slug = f"_{focus.lower().replace(' ', '-')}" if focus else ""
    filename = f"brief_{clean_name}{focus_slug}_{date_str}.md"
    output_path = os.path.join(os.path.dirname(__file__), "..", filename)
    output_path = os.path.normpath(output_path)

    focus_line = f"\n*Focus: {focus}*" if focus else ""
    with open(output_path, "w") as f:
        f.write(f"# Research Brief: {company} ({industry})\n")
        f.write(f"*Generated: {datetime.now().strftime('%d %b %Y')}*{focus_line}\n\n")
        f.write(brief)
    return output_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Value Intelligence — Research Brief Generator")
    parser.add_argument("company", help='Company name e.g. "Citibank"')
    parser.add_argument("industry", help='Industry e.g. "banking"')
    parser.add_argument("--focus", help='Optional focus area e.g. "Treasury and Trade Solutions"', default=None)
    args = parser.parse_args()

    brief = run_research(args.company, args.industry, focus=args.focus)

    if brief:
        path = save_brief(args.company, args.industry, brief, focus=args.focus)
        print(f"\nBrief saved to: {path}")
        print("\n" + "=" * 60 + "\n")
        print(brief)
    else:
        print("No brief generated.")
