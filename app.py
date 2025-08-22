# app.py
import os
import re
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
st.markdown("Upload the **Word submission** and click **Run Review**. You’ll get a downloadable Word report.")

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

# ---------------- Keys & Helpers ----------------
FIELD_ALIASES = {
    "business_name": ["Business Name"],
    "brief_description": ["Brief Description of Business", "Brief Description"],
    "problem": ["Problem", "1) Problem"],
    "value_proposition": ["Value Proposition", "2) Value Proposition"],
    "unfair_advantage": ["Unfair Advantage", "3) Unfair Advantage"],
    "customer_segments": ["Customer Segments", "4) Customer Segments"],
    "channels": ["Channels", "5) Channels"],
    "customer_relationships": ["Customer Relationships", "6) Customer Relationships"],
    "key_activities": ["Key Activities", "7) Key Activities"],
    "key_resources": ["Key Resources", "8) Key Resources"],
    "key_partners": ["Key Partners", "9) Key Partners"],
    "revenue_streams": ["Revenue Streams", "10) Revenue Streams"],
    "cost_structure": ["Cost Structure", "11) Cost Structure"],
    "kingdom_impact": ["Kingdom Impact", "12) Kingdom Impact"],
}
CANONICAL_ORDER = [
    "business_name","brief_description","problem","value_proposition","unfair_advantage",
    "customer_segments","channels","customer_relationships","key_activities","key_resources",
    "key_partners","revenue_streams","cost_structure","kingdom_impact",
]
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

def parse_docx_to_payload(doc_bytes: bytes) -> dict:
    """Parse a .docx where fields are provided under clear headings that match FIELD_ALIASES."""
    doc = Document(BytesIO(doc_bytes))
    # flatten paragraphs
    paras = [p.text.strip() for p in doc.paragraphs]
    # normalize: drop empties but keep a sentinel between sections
    # Use a finite-state collector
    alias_map = {}
    for key, aliases in FIELD_ALIASES.items():
        for a in aliases:
            alias_map[a.lower()] = key
            alias_map[(a + ":").lower()] = key

    current_key = None
    buf = {k: "" for k in FIELD_ALIASES.keys()}

    def start_key_for(heading: str):
        h = heading.strip().rstrip(":").lower()
        return alias_map.get(h)

    for line in paras:
        if not line:
            continue
        maybe = start_key_for(line)
        if maybe:
            current_key = maybe
            continue
        if current_key:
            # stop if they accidentally typed another heading inline
            if start_key_for(line):
                current_key = start_key_for(line)
                continue
            # append content
            if buf[current_key]:
                buf[current_key] += "\n" + line
            else:
                buf[current_key] = line

    # final trim
    for k in buf:
        buf[k] = (buf[k] or "").strip()

    return buf

def list_empty_blocks(payload: dict):
    # map canvas blocks only (not business name or brief description)
    mapping = {
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
    empties = []
    for title, key in mapping.items():
        val = (payload.get(key) or "").strip()
        if not val:
            empties.append(title)
    return empties

def normalize_markdown(md_text: str) -> str:
    out = []
    for raw in md_text.splitlines():
        line = raw.strip()
        if not line:
            out.append("")
            continue
        if line in ADVISORY_TEXTS:
            continue
        if line in MAJOR_SECTIONS:
            out.append("## " + line); continue
        if line in (SUBS_STANDARD + SUBS_13 + SUBS_14):
            out.append("### " + line); continue
        out.append(line)
    return "\n".join(out).strip()

def enforce_missing_for_empty_blocks(norm_md: str, empty_blocks: list[str]) -> str:
    lines = norm_md.splitlines()
    # identify section starts
    idx = [(i, lines[i][3:].strip()) for i in range(len(lines)) if lines[i].startswith("## ")]
    idx.append((len(lines), None))
    def subs_for(title):
        if title == "13) Cross-Block Observations": return SUBS_13
        if title == "14) Final Assessment": return SUBS_14
        return SUBS_STANDARD
    out = []
    i = 0
    while i < len(lines):
        if lines[i].startswith("## "):
            title = lines[i][3:].strip()
            next_i = next((j for j,(k,_) in enumerate(idx) if k == i), None)
            end = idx[next_i+1][0] if next_i is not None else len(lines)
            if title in empty_blocks:
                out.append(lines[i])  # keep the H1
                for s in subs_for(title):
                    out.append(f"### {s}")
                    out.append("• Missing/Needs input.")
                i = end
                continue
        out.append(lines[i])
        i += 1
    return "\n".join(out).strip()

# ---------------- DOCX Builder (unchanged styles) ----------------
def build_docx_from_markdown(md_text: str, founder_payload: dict) -> bytes:
    doc = Document()

    # Logo centered if present
    base_dir = os.path.dirname(__file__)
    logo_path = os.path.join(base_dir, "assets", "logo.png")
    if os.path.exists(logo_path):
        try:
            p = doc.add_paragraph(); r = p.add_run()
            r.add_picture(logo_path, width=Inches(1.5)); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        except Exception:
            pass
    # Title
    title = doc.add_heading(f"Sinapis AI Coach – BMC Review of {founder_payload.get('business_name') or '(Unnamed Business)'}", level=0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    # Description
    bd = founder_payload.get("brief_description") or "—"
    meta = doc.add_paragraph(); r1 = meta.add_run("Description: "); r1.bold = True; meta.add_run(bd)

    # Styles
    normal = doc.styles["Normal"].font; normal.name = "Calibri"; normal.size = Pt(11)
    h1 = doc.styles["Heading 1"].font; h1.name = "Calibri"; h1.size = Pt(14); h1.bold = True; h1.color.rgb = RGBColor(31,78,121)
    h2 = doc.styles["Heading 2"].font; h2.name = "Calibri"; h2.size = Pt(12); h2.bold = True; h2.color.rgb = RGBColor(0,0,0)

    for raw in md_text.splitlines():
        line = raw.strip()
        if line == "": doc.add_paragraph(""); continue
        if line.startswith("## "): doc.add_heading(line[3:].strip(), level=1); continue
        if line.startswith("### "): doc.add_heading(line[4:].strip(), level=2); continue
        if line.startswith(("• ","- ")): doc.add_paragraph(line[2:].strip(), style="List Bullet"); continue
        doc.add_paragraph(line)

    doc.add_paragraph().add_run("Advisory—Not Legal/Financial Advice.").italic = True
    buf = BytesIO(); doc.save(buf); buf.seek(0); return buf.getvalue()

def render_download_only(markdown_text: str, founder_payload: dict):
    st.success("Your AI review is ready. Click below to download the Word report.")
    docx_bytes = build_docx_from_markdown(markdown_text, founder_payload)
    st.download_button(
        label="⬇️ Download your review (Word .docx)",
        data=docx_bytes,
        file_name="Sinapis_AI_Coach_Assessment.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        use_container_width=True
    )

# ---------------- UI: Word Upload ----------------
uploaded = st.file_uploader("Upload founder submission (.docx)", type=["docx"])
submitted = st.button("Run Review", use_container_width=True, disabled=uploaded is None)

# ---------------- Run Review ----------------
if submitted and uploaded:
    with st.spinner("Generating your review…"):
        try:
            payload = parse_docx_to_payload(uploaded.read())
            empty_blocks = list_empty_blocks(payload)

            user_message = (
                "Founder Input (normalized JSON):\n"
                + str(payload)
                + "\n\nEMPTY_BLOCKS: " + str(empty_blocks)
                + "\n\nUse the response template exactly."
            )
            client = get_client()
            resp = client.chat_completions.create(  # compatibility with older SDK names
                model="gpt-4o-mini",
                temperature=0.0,
                messages=[
                    {"role": "system", "content": SINAPIS_COACH_SYS},
                    {"role": "system", "content": MARKDOWN_INSTRUCTION},
                    {"role": "system", "content": STRICT_NO_INVENTION},
                    {"role": "system", "content": "Response Template:\n" + SINAPIS_RESPONSE_TEMPLATE},
                    {"role": "user", "content": user_message},
                ],
            )
            raw_md = resp.choices[0].message.content
            norm_md = normalize_markdown(raw_md)
            final_md = enforce_missing_for_empty_blocks(norm_md, empty_blocks)
            # show only download button
            render_download_only(final_md, payload)
        except AttributeError:
            # for new SDK name
            resp = get_client().chat.completions.create(
                model="gpt-4o-mini",
                temperature=0.0,
                messages=[
                    {"role": "system", "content": SINAPIS_COACH_SYS},
                    {"role": "system", "content": MARKDOWN_INSTRUCTION},
                    {"role": "system", "content": STRICT_NO_INVENTION},
                    {"role": "system", "content": "Response Template:\n" + SINAPIS_RESPONSE_TEMPLATE},
                    {"role": "user", "content": user_message},
                ],
            )
            raw_md = resp.choices[0].message.content
            norm_md = normalize_markdown(raw_md)
            final_md = enforce_missing_for_empty_blocks(norm_md, empty_blocks)
            render_download_only(final_md, payload)
        except Exception as e:
            st.error(f"Failed to process: {e}")

# ---------------- Footer ----------------
st.caption("Advisory—Not Legal/Financial Advice.")
