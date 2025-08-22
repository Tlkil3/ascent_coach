# Sinapis AI Coach – Ascent BMC Reviewer

This Streamlit app allows founders to submit an early draft of their **Business Model Canvas**  
and receive structured feedback from the **Sinapis AI Coach**, based on the  
Ascent framework (Osterwalder BMC + Ash Maurya Lean Canvas + Kingdom Impact lens).


**What it does:** Founders upload a Business Model Canvas draft as a **Word (.docx)**. The app produces a **structured, styled Word review** using the Sinapis Ascent framework (Osterwalder BMC + Lean Canvas emphasis + Kingdom Impact lens), contextualized for **Kenya/East Africa**.  Set to use 40 mini at the moment

---

## Repo Layout
---

## Features

- **Founder-facing form** with all 12 Ascent BMC blocks (Problem, Value Proposition, Unfair Advantage… Kingdom Impact).
- AI-generated review that follows the Sinapis **rubric** and **response template**.
- Output formatted as **Markdown** with clear section/subsection headings and bullet lists.
- **Download options**:
  - Word (.docx) report with proper headings and bullet points.
  - Markdown (.md) file for portability and versioning.
- Delivered fully in-browser via **Streamlit Cloud** (no installs required for founders).

---

## Requirements

- [Streamlit](https://streamlit.io/)  
- [OpenAI Python SDK](https://pypi.org/project/openai/)  
- [python-docx](https://pypi.org/project/python-docx/)  

Install locally with:
```bash
pip install -r requirements.txt
