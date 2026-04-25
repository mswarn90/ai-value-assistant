import anthropic
import argparse
import json
import os
import re
import sys
from datetime import datetime
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(__file__))
from tools import run_search
from evidence_store import store_evidence, retrieve_evidence, count_evidence

load_dotenv()


# ── COLLECT ──────────────────────────────────────────────────────────────────

COLLECT_SYSTEM = """You are extracting structured benchmark data from web search results.

Your job: identify specific, quantified claims — ROI figures, efficiency gains, cost reductions, time savings — and extract them as structured evidence entries.

Rules:
- Extract the 6-8 highest-quality entries only — prefer specificity over quantity
- Only extract claims that have a specific number or % attached. "Significant improvement" is not evidence.
- Attribute each claim to its actual source (vendor study, analyst report, public case study)
- If the same claim appears in multiple results, extract it once with the most detailed source
- Do not fabricate or round numbers

Output ONLY a valid JSON array. No preamble, no commentary, no markdown. Each entry must match this structure exactly:

[
  {
    "claim": "specific quantified claim e.g. '40% reduction in compliance reporting effort'",
    "source": "e.g. 'Workiva, 2024 Financial Services Benchmark Report'",
    "industry": "e.g. 'financial services'",
    "value_type": "cost reduction | revenue growth | risk reduction | efficiency gain",
    "url": "source URL if available, else empty string"
  }
]"""


def run_collect(topic: str) -> int:
    client = anthropic.Anthropic()

    queries = [
        f"{topic} ROI benchmarks case study results",
        f"{topic} cost reduction efficiency statistics",
        f"{topic} Forrester Gartner analyst report",
        f"{topic} implementation results enterprise",
    ]

    print(f"\nCollecting evidence for: {topic}")
    all_results = []
    for q in queries:
        print(f"  Searching: {q}")
        all_results.append(run_search(q))

    combined = "\n\n---\n\n".join(all_results)
    # Truncate to avoid exceeding context limits while preserving coverage across all queries
    if len(combined) > 24000:
        combined = combined[:24000]

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8192,
        system=COLLECT_SYSTEM,
        messages=[{"role": "user", "content": f"Extract evidence entries from these search results:\n\n{combined}"}]
    )

    raw = response.content[0].text.strip()
    raw = re.sub(r'^```(?:json)?\s*', '', raw)
    raw = re.sub(r'\s*```$', '', raw)

    entries = json.loads(raw)
    d = datetime.now()
    date_str = f"{d.day} {d.strftime('%b')} {d.year}"
    for entry in entries:
        entry["date_collected"] = date_str

    stored = store_evidence(entries)
    print(f"  Stored {stored} entries. Library total: {count_evidence()}")
    return stored


# ── QUERY ─────────────────────────────────────────────────────────────────────

def run_query(query: str, n: int = 5):
    print(f"\nQuerying evidence library for: {query}\n")
    results = retrieve_evidence(query, n_results=n)
    if not results:
        print("No evidence found. Run 'collect' first to populate the library.")
        return

    for i, entry in enumerate(results, 1):
        print(f"{i}. {entry['claim']}")
        print(f"   Source: {entry['source']}")
        print(f"   Industry: {entry['industry']} | Value type: {entry['value_type']}")
        if entry.get("url"):
            print(f"   URL: {entry['url']}")
        print()


# ── ENRICH ────────────────────────────────────────────────────────────────────

ENRICH_SYSTEM = """You are enriching a value case document with real evidence from a benchmark library.

Your task: replace (modeled) labels on % figures with inline source citations where a strong match exists.

Rules:
- Only substitute a (modeled) label if the retrieved evidence directly supports the specific claim
- When substituting a % figure, replace (modeled) with [Source, Year] inline — e.g. 40%–60% [Workiva, 2024]
- Keep the original number or range — only update the label and add the source citation
- If retrieved evidence has a more specific number, you may use it but must note the change
- Leave (modeled) in place on $ figures — these require client data and cannot be benchmarked
- Do not change the structure or prose of the document
- Add a ## Evidence Sources section at the end listing every source cited"""


def run_enrich(value_case_path: str):
    if not os.path.exists(value_case_path):
        project_root = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
        candidate = os.path.join(project_root, value_case_path)
        if os.path.exists(candidate):
            value_case_path = candidate
        else:
            print(f"Error: File not found: {value_case_path}")
            sys.exit(1)

    with open(value_case_path) as f:
        value_case = f.read()

    total = count_evidence()
    print(f"\nEnriching: {os.path.basename(value_case_path)}")
    print(f"Evidence library: {total} entries")

    if total == 0:
        print("Evidence library is empty. Run 'collect' first.")
        sys.exit(1)

    # Retrieve evidence for each value driver section
    driver_headings = re.findall(r'###\s+(.+)', value_case)
    all_evidence, seen = [], set()
    for heading in driver_headings:
        results = retrieve_evidence(heading, n_results=3)
        for r in results:
            key = r["claim"]
            if key not in seen:
                seen.add(key)
                all_evidence.append(r)
        print(f"  Retrieved evidence for: {heading}")

    evidence_block = "\n".join(
        f"- [{e['value_type']}] {e['claim']} — {e['source']}"
        for e in all_evidence
    )

    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=ENRICH_SYSTEM,
        messages=[{
            "role": "user",
            "content": f"Value case to enrich:\n\n{value_case}\n\n---\n\nRetrieved evidence:\n\n{evidence_block}"
        }]
    )

    enriched = response.content[0].text

    d = datetime.now()
    date_str = f"{d.day}-{d.strftime('%b').lower()}-{d.year}"
    company = os.path.basename(value_case_path).replace("value-case-", "").split("-")[0]
    out_filename = f"value-case-enriched-{company}-{date_str}.md"
    out_path = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", out_filename))

    with open(out_path, "w") as f:
        f.write(enriched)

    print(f"\nEnriched value case saved to: {out_path}")
    print("\n" + "=" * 60 + "\n")
    print(enriched)


# ── ENTRY POINT ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Value Intelligence — Evidence Engine")
    subparsers = parser.add_subparsers(dest="command", required=True)

    collect_p = subparsers.add_parser("collect", help="Search for and store evidence on a topic")
    collect_p.add_argument("topic", help='Topic e.g. "financial services compliance automation"')

    query_p = subparsers.add_parser("query", help="Query the evidence library")
    query_p.add_argument("query", help='Search query e.g. "fraud detection ROI banking"')
    query_p.add_argument("--n", type=int, default=5, help="Number of results (default: 5)")

    enrich_p = subparsers.add_parser("enrich", help="Enrich a value case with retrieved evidence")
    enrich_p.add_argument("value_case", help="Path to a value case .md file")

    args = parser.parse_args()

    if args.command == "collect":
        run_collect(args.topic)
    elif args.command == "query":
        run_query(args.query, n=args.n)
    elif args.command == "enrich":
        run_enrich(args.value_case)
