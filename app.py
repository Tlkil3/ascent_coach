def build_docx_from_markdown(md_text: str, founder_payload: dict) -> bytes:
    """Map Markdown headings/bullets into a Word doc with centered logo + styles; fail gracefully if logo missing."""
    doc = Document()

    # --- BRANDING: LOGO (centered) ---
    base_dir = os.path.dirname(__file__)
    logo_path = os.path.join(base_dir, "assets", "logo.png")
    if os.path.exists(logo_path):
        try:
            paragraph = doc.add_paragraph()
            run = paragraph.add_run()
            run.add_picture(logo_path, width=Inches(1.5))  # slightly bigger, adjust size if needed
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        except Exception as e:
            st.warning(f"Logo found but could not be inserted: {e}")
            p = doc.add_paragraph()
            r = p.add_run("Logo present but could not be inserted.")
            r.italic = True
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
