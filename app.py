import streamlit as st
import fitz  # PyMuPDF
from openai import OpenAI
import os

# Title
st.set_page_config(page_title="Business Model Canvas Coach")
st.title("📊 Business Model Canvas Coach")

# File uploader
st.subheader("Upload a BMC PDF")
uploaded_file = st.file_uploader("Upload a BMC PDF", type="pdf")

# Function to extract text from PDF using PyMuPDF
def extract_text_from_pdf(file):
    with fitz.open(stream=file.read(), filetype="pdf") as doc:
        text = ""
        for page in doc:
            text += page.get_text()
    return text

# Display uploaded file and extracted text
if uploaded_file is not None:
    st.write(f"Uploaded: {uploaded_file.name}")
    extracted_text = extract_text_from_pdf(uploaded_file)
    st.subheader("Extracted BMC Text")
    st.write(extracted_text)

    # Button to assess BMC
    if st.button("Assess BMC"):
        # Load API key
        try:
            client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        except Exception as e:
            st.error("API key missing or invalid. Please add it to Streamlit secrets.")
            st.stop()

        # Prepare messages for GPT
        messages = [
            {
                "role": "user",
                "content": f"""Give constructive feedback on this BMC: ```{extracted_text}```.
Evaluate each block's clarity, coherence, and completeness. Use this framework:

1. **Customer Segments**
2. **Value Propositions**
3. **Channels**
4. **Customer Relationships**
5. **Revenue Streams**
6. **Key Resources**
7. **Key Activities**
8. **Key Partnerships**
9. **Cost Structure**

Also highlight inconsistencies—e.g., mismatches between value prop and customer segments.
Be professional, helpful, and concise."""
            }
        ]

        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=messages,
                temperature=0.7,
            )
            feedback = response.choices[0].message.content
            st.subheader("🧠 AI Feedback")
            st.markdown(feedback)
        except Exception as e:
            st.error(f"Error generating feedback: {e}")
