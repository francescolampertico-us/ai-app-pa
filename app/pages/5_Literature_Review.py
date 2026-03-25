"""
Literature Review — Streamlit Page
====================================
Key findings from the literature review on AI integration in Public Affairs.
All citations verified against source PDFs (March 2026).
"""

import streamlit as st
import sys
from pathlib import Path

TOOLKIT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(TOOLKIT_ROOT / "app"))

st.set_page_config(page_title="Literature Review", page_icon="📚", layout="wide")

from shared import inject_custom_css, sidebar_nav, page_footer

inject_custom_css()
sidebar_nav()

# =====================================================================
# Hero
# =====================================================================
st.markdown("""
# How can Generative AI be systematically integrated into day-to-day Public Affairs practice?
""")
st.caption("Interactive Literature Review — Francesco Lampertico, American University (2026)")
st.markdown(
    "This page presents the key findings from the capstone literature review. "
    "For the full interactive experience, visit the "
    "[standalone version](https://interactive-literature-review.vercel.app/)."
)

st.divider()

# =====================================================================
# Introduction — Key Stats
# =====================================================================
st.markdown("## The State of AI Adoption")

m1, m2, m3 = st.columns(3)
m1.metric("Weekly AI Use", "87%",
          help="Among workers already exposed to AI tools; n=3,200 (Workday/Hanover Research, 2026)")
m2.metric("Daily AI Use", "46%",
          help="Among workers already exposed to AI tools; n=3,200 (Workday/Hanover Research, 2026)")
m3.metric("Consumer LLM Pilots", "80%",
          help="Organizations that have explored or piloted consumer LLM tools like ChatGPT/Copilot; custom enterprise tools reach only 5% production (MIT NANDA, 2025)")

st.markdown("")
st.caption(
    "Note: The 87%/46% figures come from a sample pre-screened for AI exposure "
    "(Workday/Hanover Research, 2026; n=3,200 at organizations with $100M+ revenue). "
    "The 80% pilot rate applies to consumer LLM tools; only 5% of custom enterprise AI tools "
    "reach production deployment (MIT NANDA, 2025)."
)

st.markdown("")
st.markdown(
    "GenAI exposure is disproportionately concentrated among highly educated, "
    "highly-paid, white-collar occupations. On the AI Occupational Exposure (AIOE) index, "
    "which measures structural exposure to language modeling capabilities across 773 occupations, "
    "**Public Relations Specialists** rank **#34** and **Public Relations & Fundraising Managers** "
    "rank **#67** (Felten et al., 2023). The AIOE score measures exposure to AI capabilities, "
    "not actual adoption or job displacement risk."
)

# --- Research Gap ---
st.markdown("### The Research Gap")
g1, g2, g3, g4 = st.columns(4)
with g1:
    with st.container(border=True):
        st.markdown("**Limited Scholarship**")
        st.caption(
            "Research exists in adjacent fields like PR, but systematic studies of AI "
            "in Public Affairs are nearly nonexistent (Lebenbauer, 2024; Bitonti, 2024)."
        )
with g2:
    with st.container(border=True):
        st.markdown("**Fragmented Adoption**")
        st.caption(
            "Integration is ad-hoc and bottom-up, driven by individual experimentation "
            "rather than organizational strategy (Quorum, 2024)."
        )
with g3:
    with st.container(border=True):
        st.markdown("**No Institutionalization**")
        st.caption(
            "Organizations rely on isolated pilots. Only 5% of custom enterprise AI tools "
            "reach production deployment (MIT NANDA, 2025)."
        )
with g4:
    with st.container(border=True):
        st.markdown("**Missing Frameworks**")
        st.caption(
            "The field lacks AI-specific theory for public communication research, "
            "with five identified blind spots in the literature (Lock & Weller, 2025)."
        )

st.divider()

# =====================================================================
# Chapter 1 — AI in Public Affairs
# =====================================================================
st.markdown("## 1. AI in Public Affairs and Related Fields")
st.caption("A consolidated view of the current state of play across core and adjacent domains.")

tab_pa, tab_related = st.tabs(["Public Affairs", "Related Fields"])

with tab_pa:
    pa1, pa2 = st.columns([1, 2])
    with pa1:
        st.metric("Currently Using AI", "36%", help="Quorum State of Government Affairs Survey, 2024")
        st.metric("Open to AI (of non-users)", "77%", help="77% of the 64% not yet using AI (Quorum, 2024)")
    with pa2:
        st.markdown(
            "**36%** of public affairs professionals report currently using AI in daily work. "
            "Of the **64%** not yet using AI tools, **77%** describe themselves as "
            "\"open to using AI\" once they learn more — indicating high latent demand. "
            "Meanwhile, in-person meetings remain the most effective method for influencing "
            "policymakers, cited by 69% of respondents (Quorum, 2024)."
        )
        st.markdown(
            "The field lacks consolidated evidence on effective methods. Most studies remain "
            "conceptual or practice-oriented, rarely testing concrete interventions at the task level. "
            "Emerging work on lobbying shows that frontier models can perform parts of the influence "
            "workflow, but these remain proof-of-concept rather than fully embedded organizational "
            "settings (Bitonti, 2024; Nay, 2025; Hellert et al., 2025)."
        )

    st.markdown("#### Application Domains")
    st.caption("Based on Bitonti's (2024) analysis of PA technology platforms (FiscalNote, Quorum, KMIND)")
    d1, d2 = st.columns(2)
    with d1:
        with st.container(border=True):
            st.markdown("**Monitoring & Analysis**")
            st.caption("Turning Big Data into Smart Data (George et al., 2014; via Bitonti, 2024)")
            st.markdown(
                "Digital platforms enable automated scanning of legislative sources, "
                "semi-automatic harvesting of relevant information, and computational "
                "pattern detection across regulatory landscapes."
            )
        with st.container(border=True):
            st.markdown("**Generative Content & Drafting**")
            st.caption("AI-Assisted First Drafts")
            st.markdown(
                "GenAI can generate content including texts, images, and videos "
                "\"at least as drafts on which human professionals can work\" (Bitonti, 2024). "
                "Enables rapid message iteration for audience testing."
            )
    with d2:
        with st.container(border=True):
            st.markdown("**Stakeholder Network Analysis**")
            st.caption("Augmented Intelligence for Relational Capital")
            st.markdown(
                "Social network analysis tools map connections between policymakers, journalists, "
                "and issues — visualizing coalitions and identifying legislative champions "
                "(Bitonti, 2024, describing KMIND and Quorum platforms)."
            )
        with st.container(border=True):
            st.markdown("**Grassroots & Mobilization**")
            st.caption("Algorithmic Advocacy (Karakulle, 2025)")
            st.markdown(
                "Optimization of grassroots targeting to identify effective advocates. "
                "Includes controversial 'astroturfing' risks where AI simulates artificial "
                "public support or floods policymakers' inboxes."
            )

with tab_related:
    st.markdown(
        "A senior CCO described the industry as being \"in the foothills\" of AI adoption "
        "(Buhmann et al., 2025). Usage spiked in 2023, with 80% of PR professionals viewing AI "
        "as a 'game-changer' (USC Annenberg/WE Communications, 2023; cited in Yue et al., 2024)."
    )
    r1, r2 = st.columns(2)
    with r1:
        with st.container(border=True):
            st.markdown("**Public Relations**")
            st.markdown(
                "- Core use: content creation & ideation — drafting releases, breaking writer's block "
                "(Zararsiz, 2024; Yue et al., 2024)\n"
                "- Crisis communication: chatbot responses with factual 'instructing information' "
                "receive higher competence ratings when a request fails; empathic 'adjusting information' "
                "is more effective when the situation is resolved (Xiao & Yu, 2025)\n"
                "- Social listening and sentiment detection across media channels"
            )
    with r2:
        with st.container(border=True):
            st.markdown("**Political Communication**")
            st.markdown(
                "- Micro-targeting via psychographic profiling to target voter concerns (Bazarah, 2025)\n"
                "- 'Best Intern' model: summarizing reports & drafting manifesto-aligned content (Adi, 2023)\n"
                "- Controversy: astroturfing & social bots generating fake grassroots support "
                "(Jakubiak-Mirończuk, 2025)"
            )

    st.markdown("#### Blind Spots in Current Research")
    b1, b2, b3 = st.columns(3)
    with b1:
        with st.container(border=True):
            st.markdown("**Outcomes vs. Outputs**")
            st.caption(
                "Research measures speed and volume, not long-term trust, reputation, "
                "or strategic influence (Lock & Weller, 2025)."
            )
    with b2:
        with st.container(border=True):
            st.markdown("**Geographic Bias**")
            st.caption(
                "Heavy skew toward Global North (US/UK/EU); "
                "Global South perspectives are largely absent from the literature."
            )
    with b3:
        with st.container(border=True):
            st.markdown("**Empirical Gaps**")
            st.caption(
                "Insufficient research on how AI is actually being integrated into "
                "communication departments; most work remains theoretical or conceptual "
                "(Buhmann et al., 2025)."
            )

st.divider()

# =====================================================================
# Chapter 2 — Performance Reality
# =====================================================================
st.markdown("## 2. Performance Reality")
st.caption("The 'Jagged Frontier': massive gains in some areas, hidden traps in others.")

tab_prod, tab_wf = st.tabs(["The Productivity Leap", "PA Workflows"])

with tab_prod:
    p1, p2, p3 = st.columns(3)
    with p1:
        st.metric("Speed", "37% Faster",
                   help="Control: 27 min → Treatment: 17 min; n=444 professionals (Noy & Zhang, 2023)")
    with p2:
        st.metric("Quality", ">40% Boost",
                   help="For tasks inside the AI frontier; n=758 BCG consultants (Dell'Acqua et al., 2023)")
    with p3:
        st.metric("Skill Compression", "43% vs 17%",
                   help="Bottom-half performers gained 43%, top-half gained 17% (Dell'Acqua et al., 2023)")

    st.markdown("")
    st.markdown(
        "In a randomized experiment with 444 college-educated professionals (marketers, grant writers, "
        "consultants, analysts), access to ChatGPT reduced task completion time from 27 to 17 minutes "
        "(37%) while simultaneously improving output quality by 0.45 standard deviations. "
        "Critically, ChatGPT **compressed the productivity distribution** — lower-ability workers "
        "benefited most, with initial performance inequalities \"half-erased\" by AI access. "
        "However, the study also found that 68% of participants submitted AI output with minimal editing, "
        "suggesting **substitution rather than complementarity** (Noy & Zhang, 2023)."
    )

    st.markdown("")
    with st.container(border=True):
        st.markdown("#### The Jagged Technological Frontier")
        st.markdown(
            "In a pre-registered field experiment with **758 BCG consultants**, Dell'Acqua et al. (2023) "
            "found that AI capabilities cover an expanding but **uneven** set of knowledge work — "
            "a 'jagged frontier' where tasks of seemingly similar difficulty may fall on either side:"
        )
        jf1, jf2 = st.columns(2)
        with jf1:
            with st.container(border=True):
                st.markdown("**Inside the Frontier**")
                st.markdown(
                    "Creative product innovation tasks: consultants using GPT-4 produced "
                    "**>40% higher quality** output and completed **12% more tasks** in 22-28% less time. "
                    "Bottom-half performers improved by 43%; top-half by 17%."
                )
        with jf2:
            with st.container(border=True):
                st.markdown("**Outside the Frontier**")
                st.markdown(
                    "Business problem-solving with subtle qualitative data: AI users' correctness "
                    "dropped **19 percentage points** (from 84.5% to ~65%). Paradoxically, those with "
                    "more AI training performed *worse* (60% vs 70% correct)."
                )
        st.caption(
            "A notable side effect: AI use led to more homogenized outputs — higher quality but less "
            "diverse ideas, with implications for organizational innovation (Dell'Acqua et al., 2023)."
        )

with tab_wf:
    st.markdown(
        "Bitonti (2024) identifies four clusters of PA campaign activities where digital tools "
        "create value, based on analysis of FiscalNote, Quorum, and KMIND platforms:"
    )
    wf1, wf2 = st.columns(2)
    with wf1:
        with st.container(border=True):
            st.markdown("**Monitoring & Analysis** `Automated`")
            st.caption(
                "Turning 'big data into smart data' — automated scanning of legislative sources "
                "and computational pattern detection (Bitonti, 2024)."
            )
        with st.container(border=True):
            st.markdown("**Strategy Design** `Evidence-Informed`")
            st.caption(
                "A/B testing of messaging, scenario simulation, and coalition-building "
                "based on network analysis (Bitonti, 2024)."
            )
    with wf2:
        with st.container(border=True):
            st.markdown("**Action** `Targeted`")
            st.caption(
                "Micro-targeting, real-time tracking of message effectiveness, "
                "grassroots email campaigns, and event coordination (Bitonti, 2024)."
            )
        with st.container(border=True):
            st.markdown("**Assessment** `Measurable`")
            st.caption(
                "Measuring effectiveness, tracking interactions, and preserving "
                "'relational capital' as organizational memory (Bitonti, 2024)."
            )

    with st.container(border=True):
        st.markdown("#### The Human Persuasion Imperative")
        st.markdown(
            "Despite these capabilities, DiGiacomo (2026) emphasizes that \"the future of PA "
            "in the age of AI will be a blend of high-tech analytics and the timeless art of "
            "human persuasion.\" The Quorum (2024) survey confirms this: in-person meetings remain "
            "the most effective influence method (69% of respondents). The core value of PA tools "
            "is **augmented intelligence** — reorganizing processes that \"remain inherently human\" "
            "(Bitonti, 2024), not replacing professional judgment."
        )

st.divider()

# =====================================================================
# Chapter 3 — Frameworks & Approaches
# =====================================================================
st.markdown("## 3. Frameworks & Approaches")
st.caption("Moving from theoretical integration to practical, agentic workflows.")

tab_alloc, tab_methods, tab_tools = st.tabs(["Task Allocation", "Practical Methods", "Building the Toolkit"])

with tab_alloc:
    st.markdown("How humans and AI divide cognitive labor.")
    st.markdown("")

    a1, a2, a3 = st.columns(3)
    with a1:
        with st.container(border=True):
            st.markdown("#### Task Diversification")
            st.caption("Mollick (2024)")
            st.markdown(
                "A framework for identifying the right agentic approach:\n\n"
                "- **Just Me Tasks** — High stakes, human-centric. AI is excluded.\n"
                "- **Delegated Tasks** — Human in the loop. AI drafts, human refines.\n"
                "- **Automated Tasks** — Low stakes, high volume. AI runs autonomously."
            )
    with a2:
        with st.container(border=True):
            st.markdown("#### Centaur Model")
            st.caption("Dell'Acqua et al. (2023), after Kasparov")
            st.markdown(
                "Strategic **division** of labor — humans decide which sub-tasks are best done by "
                "each party, then **delegate** accordingly. A separation model optimized for **efficiency**. "
                "Named after Garry Kasparov's concept in chess."
            )
    with a3:
        with st.container(border=True):
            st.markdown("#### Cyborg Model")
            st.caption("Dell'Acqua et al. (2023)")
            st.markdown(
                "Deep **integration** — humans and AI intertwine efforts at the subtask level, "
                "alternating responsibilities continuously. \"Intricate integration at the very "
                "frontier of capabilities.\" Optimized for **quality**."
            )

with tab_methods:
    st.markdown("Structuring prompts and workflows for the Agentic Era.")
    st.markdown("")

    st.markdown("#### The Agentic Era Stack")
    st.caption("Mollick (2026)")
    s1, s2, s3 = st.columns(3)
    with s1:
        with st.container(border=True):
            st.markdown("**Models**")
            st.caption("Raw Intelligence (GPT-4o, Claude)")
            st.markdown("Reasoning & code generation")
    with s2:
        with st.container(border=True):
            st.markdown("**Apps**")
            st.caption("Purpose-Built Tools (Perplexity, Cursor)")
            st.markdown("Specific workflows")
    with s3:
        with st.container(border=True):
            st.markdown("**Harnesses**")
            st.caption("Integration Layer (NotebookLM, Gemini)")
            st.markdown("Context & data management")

    st.markdown("")
    st.markdown("#### Prompting Strategy Board")
    pc1, pc2, pc3 = st.columns(3)
    with pc1:
        with st.container(border=True):
            st.markdown("**Context Engineering**")
            st.caption("Architect the RAM: task descriptions, RAG, state history (Harvey, 2026)")
        with st.container(border=True):
            st.markdown("**Chain-of-Thought**")
            st.caption("Force the model to show its work, essential for logic (Ibrahim, 2025)")
    with pc2:
        with st.container(border=True):
            st.markdown("**Role Prompting**")
            st.caption("Assign a persona: 'Act as a Senior Fellow' (OpenAI, 2025)")
        with st.container(border=True):
            st.markdown("**Prompt Chaining**")
            st.caption("Break complex tasks into sequential sub-prompts (God of Prompt, 2026)")
    with pc3:
        with st.container(border=True):
            st.markdown("**Self-Critique Review**")
            st.caption("Ask the AI to critique its own work harshly before finalizing (Anthropic, 2025)")
        with st.container(border=True):
            st.markdown("**Prompt Contracts**")
            st.caption("Define success criteria, constraints, and output format upfront (God of Prompt, 2026)")

with tab_tools:
    st.markdown("The practical knowledge and patterns used to build this toolkit.")
    st.markdown("")

    t1, t2 = st.columns(2)
    with t1:
        with st.container(border=True):
            st.markdown("#### Vibe Coding")
            st.caption("Karpathy (2025); Google Cloud (2025)")
            st.markdown(
                "A development practice where the primary role shifts from writing code line-by-line "
                "to guiding an AI assistant through natural language prompts (Karpathy, 2025). "
                "Google Cloud distinguishes two modes:\n\n"
                "- **\"Pure\" vibe coding** — rapid prototyping where you trust AI output for "
                "throwaway projects and speed is the priority\n"
                "- **Responsible AI-assisted development** — the professional application where "
                "AI acts as a \"pair programmer\" but the user reviews, tests, and takes full "
                "ownership of the final product\n\n"
                "This toolkit was built entirely in the second mode: Claude Code generated code "
                "from natural-language specifications, but every tool was reviewed and tested "
                "before integration."
            )
        with st.container(border=True):
            st.markdown("#### Skills & Agent Architecture")
            st.caption("Anthropic (2025); Saraev (2025)")
            st.markdown(
                "Skills are reusable instruction bundles that encode repeatable workflows — "
                "from generating documents to orchestrating multi-step processes (Anthropic, 2025). "
                "Each skill = **instruction file** (orchestrator) + "
                "**deterministic scripts** (execution). The LLM handles decisions and "
                "error recovery; scripts handle computation. This prevents error compounding "
                "(90% accuracy per LLM step = 59% over 5 steps). Combined with subagents for "
                "code review and QA, this creates a write-review-test-fix-ship pipeline (Saraev, 2025)."
            )
    with t2:
        with st.container(border=True):
            st.markdown("#### The DOE Framework")
            st.caption("Directive-Orchestration-Execution")
            st.markdown(
                "The architecture used in this toolkit:\n\n"
                "1. **Directive** (User) — define task, constraints, output format\n"
                "2. **Orchestration** (AI) — gather data, process, reason\n"
                "3. **Execution** (System) — produce verified deliverables\n\n"
                "Grounded in truthfulness research (Shao et al., 2025) and "
                "autonomous agent design (Wang et al., 2024). Each tool follows this "
                "pattern to separate *what to do* from *how to do it* from *quality control*."
            )

st.divider()

# =====================================================================
# Connection to the Toolkit
# =====================================================================
st.markdown("## From Literature to Practice")
st.markdown(
    "This toolkit is the practical application of the literature review findings. "
    "Each tool was designed to address specific gaps and apply specific frameworks:"
)

connections = [
    {"Finding": "PA professionals need task-level tools, not generic chatbots (Bitonti, 2024)",
     "Framework": "DOE Pattern (Directive-Orchestration-Execution)",
     "Toolkit Application": "Every tool follows DOE with explicit input/output contracts"},
    {"Finding": "The Jagged Frontier — AI fails on out-of-frontier tasks (Dell'Acqua et al., 2023)",
     "Framework": "Risk Tiers + Human Review Gates",
     "Toolkit Application": "Yellow/Red tools require human verification before use"},
    {"Finding": "36% adoption, 77% latent demand among non-users (Quorum, 2024)",
     "Framework": "Task Diversification (Mollick, 2024)",
     "Toolkit Application": "Tools target 'Delegated' tasks where AI drafts and humans refine"},
    {"Finding": "AI excels at monitoring, drafting, and network analysis (Bitonti, 2024)",
     "Framework": "Bitonti's 4 PA campaign activity clusters",
     "Toolkit Application": "Media Clips, Legislative Tracker, Hearing Memo map to top PA workflows"},
    {"Finding": "PA requires 'high-tech analytics + timeless art of human persuasion' (DiGiacomo, 2026)",
     "Framework": "DiGiacomo's 5 basic PA processes",
     "Toolkit Application": "Tools augment analysis, never replace human judgment on strategy"},
]

st.dataframe(
    connections,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Finding": st.column_config.TextColumn("Literature Finding", width="large"),
        "Framework": st.column_config.TextColumn("Framework Applied", width="medium"),
        "Toolkit Application": st.column_config.TextColumn("How It Shapes the Toolkit", width="large"),
    },
)

# --- Footer ---
page_footer()
