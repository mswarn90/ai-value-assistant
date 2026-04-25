# AI Value Assistant

An agentic research and value case tool for enterprise AI engagements. Given a company and industry, it produces a structured research brief and a boardroom-ready value case — in minutes, from public data.

Built to support the pre-engagement workflow of a Value Engineer: understand the landscape, identify the pain, build the business case.

---

## What it does

Two commands, one connected workflow.

**Step 1 — Research brief**
Runs a multi-search agent against live web data to produce a structured brief: company snapshot, industry dynamics, AI adoption signals, and specific value angles grounded in public evidence.

**Step 2 — Value case**
Reads the brief and runs two sequential Claude calls — an Analyst that identifies the 2–3 highest-potential pain points, and a Builder that writes the value case: value hypothesis, quantified drivers, ROI skeleton, and executive narrative.

All figures are labeled `[HYPOTHETICAL]` or `[BENCHMARK: source]` throughout — designed as a defensible starting point for CFO conversations, not a finished model.

---

## Setup

```bash
git clone https://github.com/mswarn90/ai-value-assistant.git
cd ai-value-assistant
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file at the project root:

```
ANTHROPIC_API_KEY=your_key_here
TAVILY_API_KEY=your_key_here
```

- Anthropic API key: console.anthropic.com
- Tavily API key: tavily.com — free tier includes 1,000 searches/month

---

## Usage

**Step 1 — Generate a research brief**

```bash
python src/agent.py "Citibank" "banking"
python src/agent.py "Citibank" "banking" --focus "Treasury and Trade Solutions"
```

Saves `brief_citibank_<date>.md` to the project root.

**Step 2 — Build a value case from the brief**

```bash
# Consulting mode — analyst identifies pain points and suggests products
python src/value_case.py brief_citibank_25-apr-2026.md

# Product mode — analyst maps a named product to the identified pain points
python src/value_case.py brief_citibank_25-apr-2026.md --product "process mining"

# With deal context
python src/value_case.py brief_citibank_25-apr-2026.md --context "CFO-led cost reduction initiative"
```

Saves `value_case_citibank_<date>.md` to the project root.

---

## Sample output

**Value hypothesis**

> Citibank can reduce regulatory remediation cost, document processing latency, and financial crime exposure by deploying targeted AI automation across its compliance, document operations, and fraud detection functions, materially accelerating consent order resolution while improving operating leverage across its global Services and Banking businesses.

**Value driver (excerpt)**

> ### Compliance & Regulatory Reporting Automation
> - **Pain:** Citi is operating under a 2023 consent order tied to data and risk infrastructure deficiencies. Manual processes across compliance, legal, and risk functions slow remediation velocity and create audit exposure.
> - **Improvement:** [BENCHMARK: 40%–60% reduction in manual compliance reporting effort, based on Workiva and Accenture published case studies in regulated financial services]
> - **Estimated impact:** [HYPOTHETICAL: $150M–$350M over 3 years, incorporating direct headcount reallocation, reduced external counsel spend, and lower regulatory fine exposure]

**ROI skeleton (excerpt)**

| Metric | Year 1 | Year 2 | Year 3 |
|---|---|---|---|
| Investment | [HYPOTHETICAL: $40M–$70M] | [HYPOTHETICAL: $25M–$45M] | [HYPOTHETICAL: $20M–$35M] |
| Benefits | [HYPOTHETICAL: $80M–$180M] | [HYPOTHETICAL: $220M–$420M] | [HYPOTHETICAL: $350M–$600M] |
| Net value | [HYPOTHETICAL: $10M–$110M] | [HYPOTHETICAL: $175M–$375M] | [HYPOTHETICAL: $315M–$565M] |

---

## Project structure

```
src/
├── agent.py          Research brief — entry point
├── prompts.py        System prompt for the research agent
├── tools.py          Tavily search tool definition
├── value_case.py     Value case builder — entry point
└── value_prompts.py  Analyst and Builder prompts
```

---

## Concepts covered

| Concept | Where |
|---|---|
| Agentic tool use | `agent.py` — Claude calls Tavily in a loop until research is complete |
| System prompt design | `prompts.py` — structured output with specific evidence requirements |
| Prompt chaining | `value_case.py` — two sequential Claude calls with JSON handoff |
| Structured output | `value_prompts.py` — Analyst outputs JSON consumed by Builder |

---

## Roadmap

| Layer | Status | Description |
|---|---|---|
| Research Intelligence | Complete | Research brief from web search — company snapshot, industry dynamics, AI adoption signals, value angles |
| Value Case Builder | Complete | Value hypothesis, quantified drivers, ROI skeleton, executive narrative |
| Evidence Engine | Planned | Benchmark library, proof points, case studies — validates and compounds the value case over time |
