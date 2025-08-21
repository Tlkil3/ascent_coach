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

# ---------------- OpenAI Client ----------------
def get_client():
    api_key = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
    org_id  = st.secrets.get("OPENAI_ORG")     or os.getenv("OPENAI_ORG") or os.getenv("OPENAI_ORG_ID")
    proj_id = st.secrets.get("OPENAI_PROJECT") or os.getenv("OPENAI_PROJECT")

    if not api_key:
        st.error("Missing OPENAI_API_KEY in Streamlit Secrets.")
        st.stop()

    os.environ["OPENAI_API_KEY"] = api_key
    if org_id:
        os.environ["OPENAI_ORG_ID"] = org_id
    if proj_id:
        os.environ["OPENAI_PROJECT"] = proj_id

    return OpenAI()

client = get_client()

# Quick health check
try:
    _ = client.models.list()
    st.info("✅ OpenAI connected.")
except Exception as e:
    st.error(f"OpenAI connection failed: {e}")
    st.stop()

# ---------------- Prompts ----------------
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
""").strip()

MARKDOWN_INSTRUCTION = (
    "Return the assessment as **Markdown** using '##' for section titles and '###' for subheadings. "
    "Use bullet lists for items. Preserve the exact section order and names from the Response Template."
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

# ---------------- Light CSS ----------------
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
    """Map Markdown headings and bullets into a Word doc."""
    doc = Document()
    doc.add_heading('Sinapis AI Coach – Ascent BMC Review', level=0)
    bn = founder_payload.get("business_name") or "—"
    bd = founder_payload.get("brief_description") or "—"
    meta = doc.add_paragraph()
    meta.add_run("Business: ").bold = True; meta.add_run(bn)
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
            text = line[2:].strip()
            doc.add_paragraph(text, style="List Bullet")
        else:
            doc.add_paragraph(line)

    doc.add_paragraph().add_run("Advisory—Not Legal/Financial Advice.").italic = True

    buff = BytesIO()
    doc.save(buff)
    buff.seek(0)
    return buff.getvalue()

def render_assessment(markdown_text: str, founder_payload: dict = None):
    st.divider()
    st.subheader("AI Assessment")
    st.markdown(markdown_text)

    founder_payload = founder_payload or {}
    docx_bytes = build_docx_from_markdown(markdown_text, founder_payload)
    st.download_button(
        label="⬇️ Download as Word (.docx)",
        data=docx_bytes,
        file_name="Sinapis_AI_Coach_Assessment.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        use_container_width=True
    )
    st.download_button(
        label="⬇️ Download as Markdown (.md)",
        data=markdown_text,
        file_name="Sinapis_AI_Coach_Assessment.md",
        mime="text/markdown",
        use_container_width=True
    )

# ---------------- Run Review ----------------
if submitted:
    with st.spinner("Generating structured review…"):
        payload = build_founder_payload()
        user_message = (
            "Founder Input (normalized JSON):\n"
            + str(payload)
            + "\n\nUse the response template exactly."
        )

        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.2,
            messages=[
                {"role": "system", "content": SINAPIS_COACH_SYS},
                {"role": "system", "content": MARKDOWN_INSTRUCTION},
                {"role": "system", "content": "Response Template:\n" + SINAPIS_RESPONSE_TEMPLATE},
                {"role": "user", "content": user_message},
            ],
        )
        output = resp.choices[0].message.content
        render_assessment(output, payload)

# ---------------- Footer ----------------
st.caption("Advisory—Not Legal/Financial Advice.")
