# app.py
import os
import textwrap
from io import BytesIO

import streamlit as st
from openai import OpenAI
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

# ---------------- App Config ----------------
st.set_page_config(page_title="Sinapis AI Coach – BMC Review", page_icon="🧭", layout="wide")
st.title("Sinapis AI Coach – Ascent BMC Review")
st.markdown(
    "Founders: complete the form and click **Run Review**. "
    "You’ll receive a downloadable Word report based on the Sinapis Ascent Business Model Canvas framework."
)

# ---------------- OpenAI Client (lazy) ----------------
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

STRICT_NO_INVENTION = (
    "CRITICAL: Base the assessment ONLY on the JSON fields provided. "
    "For ANY block whose input is empty/whitespace, you MUST mark the block as Missing/Needs input. "
    "Under each of its subheadings, output a single bullet: 'Missing/Needs input.' "
    "Do NOT infer or fabricate content for empty blocks. This review is stateless and only for this submission."
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
MAJOR_SECTIONS = [
    "1) Problem","2) Value Proposition","3) Unfair Advantage","4) Customer Segments",
    "5) Channels","6) Customer Relationships","7) Key Activities","8) Key Resources",
    "9) Key Partners","10) Revenue Streams","11) Cost Structure","12) Kingdom Impact",
    "13) Cross-Block Observations","14) Final Assessment"
]
SUBS_STANDARD = ["Strengths","Weaknesses","Probing Questions","Suggested Explorations"]
SUBS_13 = ["Inconsistencies","Opportunities to Strengthen"]
SUBS_14 = ["Quick Wins","Deeper Strategic Questions","Overall Cohesiveness"]
ADVISORY_TEXTS = {
    "Advisory—Not Legal/Financial Advice.",
    "Footer: Advisory—Not Legal/Financial Advice."
}
BLOCK_FIELDS = {
    "1) Problem": "problem",
    "2) Value Proposition": "value_proposition",
    "3) Unfair Advantage": "unfair_advantage",
    "4) Customer Segments": "customer_segments",
    "5) Channels": "channels",
    "6) Customer Relationships": "customer_relationships",
    "7) Key Activities": "key_activities",
    "8) Key Resources": "key_resources",
    "9) Key Partners": "key_partners",
    "10) Revenue Streams": "revenue_streams",
    "11) Cost Structure": "cost_structure",
    "12) Kingdom Impact": "kingdom_impact",
}

def list_empty_blocks(payload: dict):
    empties = []
    for title, key in BLOCK_FIELDS.items():
        val = (payload.get(key) or "").strip()
        if not val:
            empties.append(title)
    return empties

def normalize_markdown(md_text: str) -> str:
    """Ensure known section titles/subtitles become proper Markdown headings and strip duplicated advisory lines."""
    out_lines = []
    for raw in md_text.splitlines():
        line = raw.strip()
        if not line:
            out_lines.append("")
            continue
        if line in ADVISORY_TEXTS:
            continue
        if line in MAJOR_SECTIONS:
            out_lines.append("## " + line)
            continue
        if line in (SUBS_STANDARD + SUBS_13 + SUBS_14):
            out_lines.append("### " + line)
            continue
        out_lines.append(line)
    return "\n".join(out_lines).strip()

def enforce_missing_for_empty_blocks(norm_md: str, empty_blocks: list[str]) -> str:
    """Replace content for empty blocks with canonical 'Missing/Needs input.' bullets."""
    # Build line list and section index map
    lines = norm_md.splitlines()
    sect_idx = []
    for i, ln in enumerate(lines):
        if ln.startswith("## "):
            sect_idx.append((i, ln[3:].strip()))
    sect_idx.append((len(lines), None))  # sentinel

    # Quick lookup
    start_by_title = {title: start for start, title in sect_idx if title}

    def replacement_block(title: str) -> list[str]:
        if title == "13) Cross-Block Observations":
            subs = SUBS_13
        elif title == "14) Final Assessment":
            subs = SUBS_14
        else:
            subs = SUBS_STANDARD
        out = [f"## {title}"]
        for s in subs:
            out.append(f"### {s}")
            out.append("• Missing/Needs input.")
        return out

    # Build new content with replacements
    new_lines = []
    i = 0
    while i < len(lines):
        if lines[i].startswith("## "):
            title = lines[i][3:].strip()
            # find this section's end
            # current index in sect_idx
            cur_idx = next((k for k, (pos, t) in enumerate(sect_idx) if pos == i), None)
            next_start = sect_idx[cur_idx + 1][0] if cur_idx is not None else len(lines)

            if title in empty_blocks:
                new_lines.extend(replacement_block(title))
                i = next_start
                continue
        new_lines.append(lines[i])
        i += 1

    return "\n".join(new_lines).strip()

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
    """Create a Word doc with centered logo; H1=bold+blue, H2=bold+black; bullets preserved; single footer."""
    doc = Document()

    # --- BRANDING: LOGO (centered) ---
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
            r = p.add_run("Logo present but could not be inserted."); r.italic = True
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    else:
        st.warning("Logo not found at assets/logo.png. Skipping logo in exported report.")
        p = doc.add_paragraph()
        r = p.add_run("Logo not found (assets/logo.png)"); r.italic = True
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

    # Heading 1 (major sections) -> bold + blue
    h1 = doc.styles["Heading 1"].font
    h1.name = "Calibri"; h1.size = Pt(14); h1.bold = True
    h1.color.rgb = RGBColor(31, 78, 121)  # deep blue

    # Heading 2 (subsections) -> bold + black
    h2 = doc.styles["Heading 2"].font
    h2.name = "Calibri"; h2.size = Pt(12); h2.bold = True
    h2.color.rgb = RGBColor(0, 0, 0)

    # --- BODY (Markdown already normalized/enforced) ---
    for raw in md_text.splitlines():
        line = raw.strip()
        if line == "":
            doc.add_paragraph("")
            continue
        if line.startswith("## "):
            doc.add_heading(line[3:].strip(), level=1)
        elif line.startswith("### "):
            doc.add_heading(line[4:].strip(), level=2)
        elif line.startswith(("• ", "- ")):
            doc.add_paragraph(line[2:].strip(), style="List Bullet")
        else:
            doc.add_paragraph(line)

    # --- FOOTER (add once) ---
    doc.add_paragraph().add_run("Advisory—Not Legal/Financial Advice.").italic = True

    buff = BytesIO()
    doc.save(buff)
    buff.seek(0)
    return buff.getvalue()

def render_download_only(markdown_text: str, founder_payload: dict):
    """Do not render the report inline; only show a ready message + Word download button."""
    st.success("Your AI review is ready. Click below to download the Word report.")
    docx_bytes = build_docx_from_markdown(markdown_text, founder_payload)
    st.download_button(
        label="⬇️ Download your review (Word .docx)",
        data=docx_bytes,
        file_name="Sinapis_AI_Coach_Assessment.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        use_container_width=True
    )

# ---------------- Run Review ----------------
if submitted:
    with st.spinner("Generating your review…"):
        payload = build_founder_payload()
        empty_blocks = list_empty_blocks(payload)

        user_message = (
            "Founder Input (normalized JSON):\n"
            + str(payload)
            + "\n\nEMPTY_BLOCKS: " + str(empty_blocks)
            + "\n\nUse the response template exactly."
        )
        try:
            client = get_client()
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                temperature=0.0,  # deterministic & conservative
                messages=[
                    {"role": "system", "content": SINAPIS_COACH_SYS},
                    {"role": "system", "content": MARKDOWN_INSTRUCTION},
                    {"role": "system", "content": STRICT_NO_INVENTION},
                    {"role": "system", "content": "Response Template:\n" + SINAPIS_RESPONSE_TEMPLATE},
                    {"role": "user", "content": user_message},
                ],
            )
            raw_md = resp.choices[0].message.content
            # Normalize headings + enforce Missing/Needs input for empty blocks
            norm_md = normalize_markdown(raw_md)
            final_md = enforce_missing_for_empty_blocks(norm_md, empty_blocks)
            render_download_only(final_md, payload)
        except Exception as e:
            st.error(f"OpenAI request failed: {e}")

# ---------------- Footer ----------------
st.caption("Advisory—Not Legal/Financial Advice.")
