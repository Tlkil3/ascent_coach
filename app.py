# add near the top with other imports
import re
from io import BytesIO
from docx import Document

# helper to normalize left-column labels
def normalize_label(s: str) -> str:
    if not s:
        return ""
    s = s.strip()
    s = re.sub(r"^\s*\d+\s*[\.\)\-:]?\s*", "", s)   # drop leading "1.", "1)", etc.
    s = s.rstrip(":").strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s

# REPLACE your parse_docx_to_payload with this version
def parse_docx_to_payload(doc_bytes: bytes) -> dict:
    """Parse either (A) a 2-col table file ('Section'|'Your Input') or (B) a heading-style file."""
    doc = Document(BytesIO(doc_bytes))

    # canonical fields & aliases
    FIELD_ALIASES = {
        "business_name": ["business name"],
        "brief_description": ["brief description of business", "brief description"],
        "problem": ["problem", "1) problem", "1. problem"],
        "value_proposition": ["value proposition", "2) value proposition", "2. value proposition"],
        "unfair_advantage": ["unfair advantage", "3) unfair advantage", "3. unfair advantage"],
        "customer_segments": ["customer segments", "4) customer segments", "4. customer segments"],
        "channels": ["channels", "5) channels", "5. channels"],
        "customer_relationships": ["customer relationships", "6) customer relationships", "6. customer relationships"],
        "key_activities": ["key activities", "7) key activities", "7. key activities"],
        "key_resources": ["key resources", "8) key resources", "8. key resources"],
        "key_partners": ["key partners", "9) key partners", "9. key partners"],
        "revenue_streams": ["revenue streams", "10) revenue streams", "10. revenue streams"],
        "cost_structure": ["cost structure", "11) cost structure", "11. cost structure"],
        "kingdom_impact": ["kingdom impact", "12) kingdom impact", "12. kingdom impact"],
    }
    # alias lookup
    alias_to_key = {}
    for k, aliases in FIELD_ALIASES.items():
        for a in aliases:
            alias_to_key[normalize_label(a)] = k

    # hints we want to ignore if present inside the right cell
    HINT_SNIPPETS = [
        "provide a brief description of what your business does",
        "what customer problem or need are you aiming to address",
        "what are you offering to address the problem",
        "what is your uniqueness",
        "which customer groups are you targeting",
        "through what means do you reach your target customers",
        "what type of relationship do you want",
        "what tasks are vital for successful delivery",
        "what assets are essential to make your business model work",
        "which external organizations or individuals are essential",
        "how does your business earn revenue from each customer segment",
        "what are the defining characteristics of your cost structure",
        "where and how are you intentionally looking to make impact",
    ]

    def clean_value(text: str) -> str:
        lines = [ln.strip() for ln in (text or "").splitlines()]
        out = []
        for ln in lines:
            low = ln.lower()
            if not ln:
                continue
            if any(h in low for h in HINT_SNIPPETS):
                continue
            out.append(ln)
        return "\n".join(out).strip()

    # initialize output buffer
    buf = {k: "" for k in FIELD_ALIASES.keys()}

    # ---- (A) TABLE PARSER: handle two-column “Section | Your Input” format ----
    if doc.tables:
        for table in doc.tables:
            for row in table.rows:
                if len(row.cells) < 2:
                    continue
                left = normalize_label(row.cells[0].text)
                right = clean_value(row.cells[1].text)

                if not left:
                    continue
                key = alias_to_key.get(left)
                if key:
                    # prefer non-empty content; don’t overwrite with empty
                    if right:
                        buf[key] = right
        # if we extracted anything non-empty, return now
        if any(v.strip() for v in buf.values()):
            return buf
        # else fall through to paragraph parser (some files mix both)

    # ---- (B) PARAGRAPH PARSER: our heading-style template ----
    current_key = None
    for p in doc.paragraphs:
        text = (p.text or "").strip()
        norm = normalize_label(text)
        if not text:
            continue
        if norm in alias_to_key:
            current_key = alias_to_key[norm]
            continue
        if current_key:
            # stop if they typed a new heading inline
            if norm in alias_to_key:
                current_key = alias_to_key[norm]
                continue
            cleaned = clean_value(text)
            if cleaned:
                buf[current_key] = (buf[current_key] + "\n" + cleaned).strip()

    return buf
