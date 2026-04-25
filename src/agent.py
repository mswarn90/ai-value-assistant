import anthropic
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(__file__))
from prompts import SYSTEM_PROMPT
from tools import SEARCH_TOOL, run_search

load_dotenv()


def run_research(company: str, industry: str) -> str:
    client = anthropic.Anthropic()
    messages = [
        {
            "role": "user",
            "content": f"Research {company} in the {industry} industry and produce a structured research brief."
        }
    ]

    print(f"\nResearching {company} ({industry})...")

    while True:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=[
                {
                    "type": "text",
                    "text": SYSTEM_PROMPT,
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
                    print(f"  Searching: {block.input['query']}")
                    result = run_search(block.input["query"])
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result
                    })
            messages.append({"role": "user", "content": tool_results})

    return ""


def save_brief(company: str, industry: str, brief: str) -> str:
    date_str = datetime.now().strftime("%d-%b-%Y").lower()
    clean_name = company.strip('"\'').lower().replace(' ', '-')
    filename = f"brief_{clean_name}_{date_str}.md"
    output_path = os.path.join(os.path.dirname(__file__), "..", filename)
    output_path = os.path.normpath(output_path)
    with open(output_path, "w") as f:
        f.write(f"# Research Brief: {company} ({industry})\n")
        f.write(f"*Generated: {datetime.now().strftime('%d %b %Y')}*\n\n")
        f.write(brief)
    return output_path


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python src/agent.py \"Company Name\" \"Industry\"")
        print('Example: python src/agent.py "Celonis" "process mining"')
        sys.exit(1)

    company = sys.argv[1]
    industry = sys.argv[2]

    brief = run_research(company, industry)

    if brief:
        path = save_brief(company, industry, brief)
        print(f"\nBrief saved to: {path}")
        print("\n" + "=" * 60 + "\n")
        print(brief)
    else:
        print("No brief generated.")
