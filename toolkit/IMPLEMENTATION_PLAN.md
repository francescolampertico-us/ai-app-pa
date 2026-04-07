# Implementation Plan — Public Affairs AI Tools Repository (Repo-First, App-Compatible)

## 0) Outcome and design principles

### Goal
Create a GitHub repository that becomes the **single source of truth** for your public affairs AI toolset: tool definitions, reusable skills, workflows, governance, and evaluation fixtures — so tools are maintainable, portable, and can later be loaded into an app (Antigravity or other).

### Two success modes
- **Mode A (Repo ships, app optional):** the repo itself is a complete capstone artifact: documented tools + guardrails + evaluation.
- **Mode B (Repo + App):** the app becomes a UI/runtime that reads tool definitions from the repo.

### Non-goals (for now)
- Building a perfect automated evaluation framework
- Creating a complex plugin architecture
- Supporting every file format and data source  
(We start simple and scalable.)

---

## 1) Repository setup (GitHub + local)

### 1.1 Create the GitHub repository
**Deliverable:** Empty GitHub repo created.

**Rules**
- Create repo **empty** (no README, no license, no gitignore) to avoid initial merge conflicts.
- Decide visibility (Private recommended if tools include sensitive client-like examples).

**Definition of Done**
- Repo exists and you have the clone URL.

### 1.2 Local Git configuration (one-time)
**Deliverable:** Git is installed + configured.

**Checklist**
- `git --version` works
- `git config --global user.name "Your Name"`
- `git config --global user.email "your@email"`

### 1.3 Clone and create baseline commit
**Deliverable:** Repo cloned locally, first commit pushed.

**Definition of Done**
- `main` branch has an “initial scaffold” commit.

---

## 2) Create the repo scaffold (structure + templates)

### 2.1 Folder structure (minimal but scalable)
Create this structure:
pa-ai-tools/
README.md
IMPLEMENTATION_PLAN.md
tool-registry.yaml
STYLE_GUIDE.md
RISK_POLICY.md
CONTRIBUTING.md
LICENSE
.gitignore

tools/
skills/
workflows/
research/
templates/
tool/  
**Purpose**
- `tools/` = tool packages (spec + skill + examples + eval)
- `skills/` = reusable instruction blocks shared across tools
- `workflows/` = multi-tool playbooks
- `research/` = capstone materials (notes, interview learnings, bibliography, etc.)
- `templates/tool/` = copy-paste starter for new tools

### 2.2 Create tool template (the “Tool Contract” starter)
**Deliverable:** Template files that every tool will copy.

Inside `templates/tool/`:
- `tool.yaml` (metadata + input/output contract + risk)
- `spec.md` (human-readable “tool card”)
- `skill.md` (reusable instruction core)
- Optional placeholders: `examples/` and `eval/` folders (you can create these when copying)

**Definition of Done**
- You can create a new tool by copying `templates/tool` and editing 3 files.

---

## 3) Establish governance early (style + risk)

This prevents later chaos when you have 10 tools with different voices and safety assumptions.

### 3.1 `STYLE_GUIDE.md` (house style)
**Deliverable:** A single source of truth for:
- Tone (internal memo vs external lines)
- Formatting rules (headings, bullets, tables, length limits)
- “Always include” sections for PA outputs (e.g., *Assumptions & Unknowns*)
- Citation posture (what you must verify; no invented facts)

**Definition of Done**
- You can point to STYLE_GUIDE.md and say “all tools follow this”.

### 3.2 `RISK_POLICY.md` (green/yellow/red)
**Deliverable:** A lightweight policy that defines:
- **Green**: ideation/internal notes only
- **Yellow**: internal distribution allowed with review
- **Red**: external-facing, legal/regulatory claims, sensitive reputational outputs → mandatory signoff

Include:
- Review checklist (names/titles/dates, factual claims, jurisdiction mismatch)
- “Never do” rules (e.g., never fabricate stakeholders, never assert uncertain claims as facts)

**Definition of Done**
- Every tool declares a risk level and a review requirement.

---

## 4) Migrate one existing Antigravity tool (make it the “gold standard”)

This is the key move. Once one tool is packaged correctly, scaling becomes mechanical.

### 4.1 Choose the first tool
Pick the tool that is:
- already working well
- representative of your typical PA outputs
- not overly complex

**Deliverable:** Tool selected (Tool #1).

### 4.2 Export the reality from Antigravity
From the working Antigravity implementation, capture:
- the exact prompt/instructions (and any system-like constraints you use)
- required inputs and optional inputs
- 2–3 “known good” runs: input → output
- edge cases you’ve seen (missing context, ambiguous jurisdiction, etc.)

**Deliverable:** A raw export (even just pasted into a local note).

### 4.3 Package it into the repo
Create: `tools/<tool_id>/` containing:

Minimum required:
- `tool.yaml`
- `spec.md`
- `skill.md`
- `examples/example_01_input.md`
- `examples/example_01_output.md`
- `eval/case_01.md` … `eval/case_05.md` (start with 5)

**Definition of Done**
- Someone unfamiliar with Antigravity can run the tool manually using the spec + skill.
- Outputs are consistent with the contract.
- There’s at least 1 example and 5 eval cases.

### 4.4 Add it to `tool-registry.yaml`
**Deliverable:** Registry updated with Tool #1.

**Definition of Done**
- A future app could list tools by reading tool-registry.

---

## 5) Create the “tool addition workflow” (repeatable process)

Once Tool #1 is done, you formalize how new tools are added.

### Standard process to add Tool #N
1) Copy `templates/tool` → `tools/<tool_id>/`
2) Write `tool.yaml` (inputs/outputs + risk)
3) Write `spec.md` (when to use, failure modes, review checklist)
4) Write `skill.md` (instruction core + exact output headings)
5) Add 2 examples
6) Add 5–10 eval cases
7) Update `tool-registry.yaml`
8) Commit with message: `Add <tool_id> tool package`

**Definition of Done**
- Every tool has the same “minimum viable package”.

---

## 6) Evaluation strategy (lightweight but real)

You’re not trying to “prove the model is perfect.” You’re building a harness for:
- regression prevention (tool doesn’t drift)
- consistency (format and caveats)
- safety (no fabrication)

### 6.1 Per-tool eval cases
In `tools/<tool_id>/eval/`, each case should include:
- input
- acceptance criteria (bulleted checks), e.g.:
  - includes required headings
  - flags unknowns explicitly
  - doesn’t invent names or facts
  - maintains tone constraints
  - provides next-step verification prompts

### 6.2 Optional later upgrade
Later, you can add `scripts/` with a simple runner that checks headings/sections, but it’s optional at first.

**Definition of Done**
- You can re-run test inputs and spot “did quality degrade?”

---

## 7) Versioning and release discipline

Keep it simple and consistent.

### 7.1 Version rules
- Each tool has its own version in `tool.yaml`
- Increment:
  - patch: wording tweaks, minor formatting changes
  - minor: new output sections or behavior changes
  - major: breaking contract change (rename required headings, restructure output)

### 7.2 Changelog (optional but useful)
Add a `CHANGELOG.md` later if you like; not required day one.

**Definition of Done**
- You can track when and why a tool changed.

---

## 8) Workflow documentation (so the repo “teaches”)

### 8.1 Workflows folder
Create `workflows/` documents that describe multi-step flows, e.g.:
- Weekly policy scan → summarize → impact assessment → internal brief → draft lines-to-take

**Deliverable:** At least 1 workflow doc once you have 3+ tools.

**Definition of Done**
- The repo reads like an operating manual, not just files.

---

## 9) App-readiness (without building the app yet)

If you want to keep the door open to an Antigravity-based app, you design the repo so it can be consumed later.

### 9.1 App-facing conventions
- `tool-registry.yaml` remains the canonical index
- each tool folder is self-contained
- output contracts are explicit (headings)
- risk policy is standardized (green/yellow/red)

**Definition of Done**
- An app can “load” tools without you rewriting everything.

---

## 10) Fallback plan if the app never ships

If app build pauses, the repo still becomes a polished final output by adding:
- a strong `README.md` explaining:
  - what tools exist
  - how to use them
  - what risk controls exist
  - how evaluation works
- 1–2 workflows
- 5–10 tools fully packaged
- “tool catalog” summary table in README

**Definition of Done**
- The repo stands alone as a comprehensive, reusable toolkit.

---

## Immediate next action sequence (do this first)

1) Create empty GitHub repo  
2) Clone locally  
3) Create scaffold + templates + style/risk docs  
4) Commit/push “Initial scaffold”  
5) Migrate ONE working Antigravity tool as the gold standard  
6) Commit/push “Add first tool package”  
MD 
