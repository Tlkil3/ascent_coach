
import streamlit as st
import docx
import openai
import tempfile
from docx.shared import Pt, RGBColor
from docx.enum.style import WD_STYLE_TYPE
import os

# Load API key from Streamlit secrets
openai.api_key = st.secrets["OPENAI_API_KEY"]

# === Helper Functions ===

def extract_bmc_sections_from_docx(docx_file):
    doc = docx.Document(docx_file)
    sections = {}
    current_heading = None
    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue
        if text[0].isdigit() and '.' in text:
            current_heading = text
            sections[current_heading] = ""
        elif current_heading:
            sections[current_heading] += text + " "
    return sections

def get_business_name_and_description(docx_file):
    doc = docx.Document(docx_file)
    business_name = ""
    description = ""
    for para in doc.paragraphs:
        text = para.text.strip()
        if text.lower().startswith("business name:"):
            business_name = text.split(":", 1)[1].strip()
        elif text.lower().startswith("business description:"):
            description = text.split(":", 1)[1].strip()
        if business_name and description:
            break
    return business_name, description

def generate_feedback(prompt):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a business model canvas evaluation expert helping Kenyan entrepreneurs improve their thinking."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        return response.choices[0].message["content"]
    except Exception as e:
        return f"Error generating feedback: {e}"

def write_feedback_to_docx(business_name, feedback_dict):
    doc = docx.Document()

    # Define custom style for blue bold headers
    styles = doc.styles
    if "BlueBold" not in styles:
        blue_bold_style = styles.add_style("BlueBold", WD_STYLE_TYPE.PARAGRAPH)
        font = blue_bold_style.font
        font.bold = True
        font.color.rgb = RGBColor(0, 102, 204)  # Blue color
        font.size = Pt(12)

    # Title
    doc.add_heading(f"{business_name} - Business Model Canvas Assessment", level=1)

    for section, feedback in feedback_dict.items():
        doc.add_paragraph(section, style="BlueBold")
        doc.add_paragraph(feedback.strip())

    # Save to temporary path
    output_path = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
    doc.save(output_path.name)
    return output_path.name

# === Streamlit App ===

st.title("Business Model Canvas Coach (Ascent Coach)")
st.write("Upload a Word document with your completed BMC to receive tailored feedback.")

uploaded_file = st.file_uploader("Upload your Word (.docx) file", type="docx")

if uploaded_file:
    with st.spinner("Analyzing your Business Model Canvas..."):
        business_name, business_description = get_business_name_and_description(uploaded_file)
        sections = extract_bmc_sections_from_docx(uploaded_file)

        feedback_dict = {}
        for section_title, section_content in sections.items():
            user_prompt = (
                f"The business is called {business_name}.
"
                f"It operates in Kenya and is described as follows: {business_description}
"
                f"Below is the content for the BMC section titled '{section_title}'.
"
                "Please evaluate it, identify weaknesses or areas to improve, "
                "raise thoughtful questions the entrepreneur should consider, "
                "and provide specific suggestions.
"
                "Respond clearly and thoroughly.

"
                f"Section content:
"""
{section_content}
""""
            )
            feedback = generate_feedback(user_prompt)
            feedback_dict[section_title] = feedback

        docx_path = write_feedback_to_docx(business_name, feedback_dict)

    st.success("Assessment complete! Download your feedback below.")
    st.download_button(
        label="Download Feedback (Word doc)",
        data=open(docx_path, "rb"),
        file_name=f"{business_name}_BMC_Feedback.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
