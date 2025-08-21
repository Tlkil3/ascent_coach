# app.py
import os
import textwrap
from io import BytesIO

import streamlit as st
from openai import OpenAI
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

# ---------------- App Config ----------------
st.set_page_config(page_title="Sinapis AI Coach – BMC Review", page_icon="🧭", layout="wide")
st.title("Sinapis AI Coach – Ascent BMC Review")
st.markdown(
    "Founders: complete the form and click **Run Review**. "
    "You’ll receive structured feedback using the Sinapis Ascent Business Model Canvas framework."
)

# ---------------- OpenAI Client (lazy, non-blocking on load) ----------------
def get_client():
    api_key = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
    org_id  = st.secrets.get("OPENAI_ORG")     or os.getenv("OPENAI_ORG") or os.getenv("OPENAI_ORG_ID")
    proj_id = st.secrets.get("OPENAI_PROJECT") or os.getenv("OPENAI_PROJECT")

    if not api_key:
        st.error("Missing OPENAI_API_KEY in Streamlit Secrets.")
        st.stop()

    # Env vars so SDK finds them
    os.environ["OPENAI_API_KEY"] = api_key
    if org_id:
        os.environ["OPENAI_ORG_ID"] = org_id
    if proj_id:
        os.environ["OPENAI_PROJECT"] = proj_id

    # Add a request timeout so calls don't hang indefinitely (seconds)
    return OpenAI(timeout=30.0)

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

MARKDOWN_INSTRUCTION = (
    "Return the assessment as Markdown. "
    "Use '##' for major sections (1) Problem … 14) Final Assessment). "
    "Use '###' for subheadings (Strengths, Weaknesses, Probing Questions, Suggested Explorations; "
    "and under Final Assessment: Quick Wins, Deeper Strategic Questions, Overall Cohesiveness). "
    "Use bullet lists for items under each subheading. Do not use bold for subheadings."
)

SINAPIS_RESPONSE_TEMPLATE = textwrap.dedent("""
Use exactly these headings and order:

1) Problem
   Strengths
   Weaknesses
   Probing Questions
   Suggested Explorations
2) Value Proposition
   Strengths
   Weaknesses
   Probing Questions
   Suggested Explorations
3) Unfair Advantage
   Strengths
   Weaknesses
   Probing Questions
   Suggested Explorations
4) Customer Segments
   Strengths
   Weaknesses
   Probing Questions
   Suggested Explorations
5) Channels
   Strengths
   Weaknesses
   Probing Questions
   Suggested Explorations
6) Customer Relationships
   Strengths
   Weaknesses
   Probing Questions
   Suggested Explorations
7) Key Activities
   Strengths
   Weaknesses
   Probing Questions
   Suggested Explorations
8) Key Resources
   Strengths
   Weaknesses
   Probing Questions
   Suggested Explorations
9) Key Partners
   Strengths
   Weaknesses
   Probing Questions
   Suggested Explorations
10) Revenue Streams
   Strengths
   Weaknesses
   Probing Questions
   Suggested Explorations
11) Cost Structure
   Strengths
   Weaknesses
   Probing Questions
   Suggested Explorations
12) Kingdom Impact
   Strengths
   Weaknesses
   Probing Questions
   Suggested Explorations

13) Cross-Block Observations
   Inconsistencies
   Opportunities to Strengthen

14) Final Assessment
   Quick Wins
   Deeper Strategic Questions
   Overall Cohesiveness

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
    """Create a Word doc with centered logo + styled headings/bullets; warn if logo missing."""
    doc = Document()

    # --- BRANDING: LOGO (centered above title) ---
    base_dir = os.path.dirname(__file__)
    logo_path = os.path.join(base_dir, "assets", "logo.png")
    if os.path.exists(logo_path):
        try:
            para = doc.add_paragraph()
            run = para.add_run()
            run.add_picture(logo_path, width=Inches(1.5))
            para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        except Exception as e:
            st.warning(f"Logo found but could not be inserted: {e}")
            p = doc.add_paragraph()
            r = p.add_run("Logo present but could not be inserted.")
            r.italic = True
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    else:
        st.warning("Logo not found at assets/logo.png. Skipping logo in exported report.")
        p = doc.add_paragraph()
        r = p.add_run("Logo not found (assets/logo.png)")
        r.italic = True
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # --- TITLE (dynamic, centered) ---
    business_title = founder_payload.get("business_name") or "(Unnamed Business)"
    title = doc.add_heading(f"Sinapis AI Coach – BMC Review of {business_title}", level=0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # --- DESCRIPTION LINE ---
    bd = founder_payload.get("brief_description") or "—"
    meta = doc.add_paragraph()
    r1 = meta.add_run("Description: "); r1.bold = True
    meta.add_run(bd)

    # --- GLOBAL STYLES ---
    normal = doc.styles["Normal"].font
    normal.name = "Calibri"; normal.size = Pt(11)

    h1 = doc.styles["Heading 1"].font
    h1.name = "Calibri"; h1.size = Pt(14); h1.bold = True

    h2 = doc.styles["Heading 2"].font
    h2.name = "Calibri"; h2.size = Pt(12); h2.bold = True

    # --- BODY FROM MARKDOWN ---
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

    # --- FOOTER ---
    doc.add_paragraph().add_run("Advisory—Not Legal/Financial Advice.").italic = True

    buf = BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf.getvalue()

def render_assessment(markdown_text: str, founder_payload: dict = None):
    st.divider()
    name_for_title = (founder_payload or {}).get("business_name") or "(Unnamed Business)"
    st.subheader(f"BMC Review of {name_for_title}")
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

        try:
            client = get_client()  # create client only when needed
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
        except Exception as e:
            st.error(f"OpenAI request failed: {e}")

# ---------------- Footer ----------------
st.caption("Advisory—Not Legal/Financial Advice.")
