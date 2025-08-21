# app.py
import os
import textwrap
from io import BytesIO

import streamlit as st
from openai import OpenAI
from docx import Document

# ---------------- App Config ----------------
st.set_page_config(page_title="Sinapis AI Coach – BMC Review", page_icon="🧭", layout="wide")
st.title("Sinapis AI Coach – Ascent BMC Review")
st.markdown(
    "Founders: complete the form and click **Run Review**. "
    "You’ll receive structured feedback using the Sinapis Ascent Business Model Canvas framework."
)

# ---------------- OpenAI Client (robust across SDK versions) ----------------
def get_client():
    api_key = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
    org_id  = st.secrets.get("OPENAI_ORG")     or os.getenv("OPENAI_ORG") or os.getenv("OPENAI_ORG_ID")
    proj_id = st.secrets.get("OPENAI_PROJECT") or os.getenv("OPENAI_PROJECT")

    if not api_key:
        st.error("Missing OPENAI_API_KEY in Streamlit Secrets.")
        st.stop()

    # Set env vars so the SDK auto-picks them up (avoids constructor differences across versions)
    os.environ["OPENAI_API_KEY"] = api_key
    if org_id:
        os.environ["OPENAI_ORG_ID"] = org_id
    if proj_id:
        os.environ["OPENAI_PROJECT"] = proj_id

    return OpenAI()  # reads from env

client = get_client()

# Quick health check
try:
    _ = client.models.list()
    st.info("✅ OpenAI connected.")
except Exception as e:
    st.error(f"OpenAI connection failed: {e}")
    st.stop()

# ---------------- Prompts (Phase 1: prompt-only) ----------------
SINAPIS_COACH_SYS = textwrap.dedent("""
You are **Sinapis AI Coach**, reviewing founder submissions using the Sinapis Ascent Business Model Canvas.
Context:
- Audience: Post-revenue, high-growth SMEs in frontier markets (starting with Kenya).
- Methodology: Osterwalder BMC + Ash Maurya Lean Canvas emphasis on problem-solution fit + Sinapis Kingdom Impact lens.

Tone & Style:
- Encouraging and growth-oriented, but willing to give direct critique.
- Diagnostic + light prescriptive: identify gaps and suggest *categories* of improvements (not company-specific instructions).
- Ask probing questions to guide the founder’s next steps.
- NEVER invent content for missing blocks. If a block is blank or unclear, explicitly mark it as “Missing/Needs input.”
- Be concise where possible; avoid jargon.

Evaluation Rubric (apply to each block):
- Problem: Is it a must-have? Evidence it’s worth solving? Aware of alternatives? Avoid innovator’s bias.
- Value Proposition: Clear, compelling, differentiated (≤3 sentences). Why better than alternatives?
- Unfair Advantage: Defensible uniqueness (IP, network effects, brand, economies of scale, team). Durability over time.
- Customer Segments: Specific, sized, reachable, willing & able to pay. Alignment with value prop.
- Channels: Sales/distribution + communication; fit with customer preferences; cost-effectiveness; integrated touchpoints.
- Customer Relationships: Acquisition, retention, upsell; transactional vs relational; cost vs value.
- Key Activities: Core tasks linked to value, channels, relationships, revenue; distinguish from partner-able tasks.
- Key Resources: Human, physical, IP, financial; prioritize scarce/critical items.
- Key Partners: Critical external orgs; why they matter; fit with gaps in resources/activities; values-aligned.
- Revenue Streams: Sources by segment; pricing model logic; margins/unit economics; concentration risk.
- Cost Structure: Major costs & drivers; fixed vs variable; unit costs; runway; control measures.
- Kingdom Impact: Intentionality across Economic, Social, Spiritual, Environmental; tie to operations and growth strategy.

Cross-Block Checks (always run):
- Value Prop ↔ Customer Segments
- Segments ↔ Channels
- Value Prop ↔ Revenue
- Activities ↔ Resources
- Partners ↔ Resources/Activities
- Costs ↔ Revenue
- Kingdom Impact ↔ All Blocks

Formatting Rules:
- Use bullet points under each subheading; keep to 3–6 bullets per list when possible.
- If a field provided by the founder is ambiguous, explicitly note “Ambiguous” and ask a clarifying question.
- DO NOT include legal or financial advice; include a footer “Advisory—Not Legal/Financial Advice.”
""").strip()

# Force the model to return clean Markdown with proper headings/bullets
MARKDOWN_INSTRUCTION = (
    "Return the assessment as **Markdown** using '##' for section titles and '###' for subheadings. "
    "Use true bullet lists (• or -) for items. Preserve the exact section order and names from the Response Template."
)

SINAPIS_RESPONSE_TEMPLATE = textwrap.dedent("""
Use exactly these headings and order:

1) Problem
   • Strengths
   • Weaknesses
   • Probing Questions
   • Suggested Explorations
2) Value Proposition
   • Strengths
   • Weaknesses
   • Probing Questions
   • Suggested Explorations
3) Unfair Advantage
   • Strengths
   • Weaknesses
   • Probing Questions
   • Suggested Explorations
4) Customer Segments
   • Strengths
   • Weaknesses
   • Probing Questions
   • Suggested Explorations
5) Channels
   • Strengths
   • Weaknesses
   • Probing Questions
   • Suggested Explorations
6) Customer Relationships
   • Strengths
   • Weaknesses
   • Probing Questions
   • Suggested Explorations
7) Key Activities
   • Strengths
   • Weaknesses
   • Probing Questions
   • Suggested Explorations
8) Key Resources
   • Strengths
   • Weaknesses
   • Probing Questions
   • Suggested Explorations
9) Key Partners
   • Strengths
   • Weaknesses
   • Probing Questions
   • Suggested Explorations
10) Revenue Streams
   • Strengths
   • Weaknesses
   • Probing Questions
   • Suggested Explorations
11) Cost Structure
   • Strengths
   • Weaknesses
   • Probing Questions
   • Suggested Explorations
12) Kingdom Impact
   • Strengths
   • Weaknesses
   • Probing Questions
   • Suggested Explorations

13) Cross-Block Observations
   • Inconsistencies (list)
   • Opportunities to Strengthen (list)

14) Final Assessment
   • Quick Wins (3–5 bullets)
   • Deeper Strategic Questions (5–7 bullets)
   • Overall Cohesiveness (short paragraph)

Footer: Advisory—Not Legal/Financial Advice.
""").strip()

# ---------------- Light CSS for spacing ----------------
st.markdown("""
<style>
h2 { margin-top: 1.0rem; }
h3 { margin-top: 0.6rem; }
</style>
""", unsafe_allow_html=True)

# ---------------- Founder Form ----------------
with st.form("bmc_form"):
    st.subheader("Founder Submission")
    col1, col2 = st.columns(2)
    with col1:
        business_name = st.text_input("Business Name")
    with col2:
        brief_description = st.text_area("Brief Description of Business", height=80)

    problem = st.text_area("1) Problem – What customer problem/need are you addressing?", height=150)
    value_proposition = st.text_area("2) Value Proposition – What are you offering?", height=150)
    unfair_advantage = st.text_area("3) Unfair Advantage – What is not easily replicated?", height=120)
    customer_segments = st.text_area("4) Customer Segments – Which groups are you targeting?", height=150)
    channels = st.text_area("5) Channels – How do you reach/deliver to customers?", height=120)
    customer_relationships = st.text_area("6) Customer Relationships – How will you acquire/retain/upsell?", height=120)
    key_activities = st.text_area("7) Key Activities – Core tasks to deliver the value proposition", height=120)
    key_resources = st.text_area("8) Key Resources – Critical assets (human, physical, IP, financial)", height=120)
    key_partners = st.text_area("9) Key Partners – External orgs/individuals essential to the model", height=120)
    revenue_streams = st.text_area("10) Revenue Streams – Sources, pricing model, margins", height=140)
    cost_structure = st.text_area("11) Cost Structure – Major costs, fixed vs variable, unit costs, runway", height=140)
    kingdom_impact = st.text_area("12) Kingdom Impact – Economic, Social, Spiritual, Environmental", height=140)

    submitted = st.form_submit_button("Run Review")

# ---------------- Helpers ----------------
def build_founder_payload():
    return {
        "business_name": (business_name or "").strip(),
        "brief_description": (brief_description or "").strip(),
        "problem": (problem or "").strip(),
        "value_proposition": (value_proposition or "").strip(),
        "unfair_advantage": (unfair_advantage or "").strip(),
        "customer_segments": (customer_segments or "").strip(),
        "channels": (channels or "").strip(),
        "customer_relationships": (customer_relationships or "").strip(),
        "key_activities": (key_activities or "").strip(),
        "key_resources": (key_resources or "").strip(),
        "key_partners": (key_partners or "").strip(),
        "revenue_streams": (revenue_streams or "").strip(),
        "cost_structure": (cost_structure or "").strip(),
        "kingdom_impact": (kingdom_impact or "").strip(),
    }

def build_docx_from_markdown(md_text: str, founder_payload: dict) -> bytes:
    """Very light MD-to-DOCX mapping: H2->Heading 1, H3->Heading 2, bullets->List Bullet."""
    doc = Document()
    # Title + meta
    doc.add_heading('Sinapis AI Coach – Ascent BMC Review', level=0)
    bn = founder_payload.get("business_name") or "—"
    bd = founder_payload.get("brief_description") or "—"
    meta = doc.add_paragraph()
    meta.add_run("Business: ").bold = True; meta.add_run(bn)
    meta.add_run("   |   ")
    meta2 = doc.add_paragraph()
    meta2.add_run("Description: ").bold = True; meta2.add_run(bd)

    for raw in md_text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("## "):
            doc.add_heading(line[3:].strip(), level=1)
        elif line.startswith("### "):
            doc.add_heading(line[4:].strip(), level=2)
        elif line.startswith(("• ", "- ")):
