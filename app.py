import openai
import streamlit as st
import os
import fitz  # PyMuPDF
from openpyxl import load_workbook

# Set OpenAI credentials
openai.api_key = st.secrets["OPENAI_API_KEY"]
openai.organization = st.secrets["OPENAI_ORG"]
openai.project = st.secrets["OPENAI_PROJECT"]

st.title("Business Model Canvas Coach")

st.markdown("Upload a BMC PDF")

uploaded_file = st.file_uploader("Upload a BMC PDF", type="pdf")

if uploaded_file is not None:
    file_path = f"/tmp/{uploaded_file.name}"
    with open(file_path, "wb") as f:
        f.write(uploaded_file.read())

    # Extract text from the uploaded PDF
    doc = fitz.open(file_path)
    text = ""
    for page in doc:
        text += page.get_text()

    st.subheader("Extracted BMC Text")
    st.text(text)

    # Use GPT to analyze and give constructive feedback
    with st.spinner("Analyzing..."):
        user_prompt = (
            "Give constructive feedback on this BMC:\n\n"
            + text +
            "\n\nHighlight any inconsistencies or gaps across the blocks "
            "(e.g., a mismatch between the value proposition and the customer "
            "segment, or unclear revenue streams)."
        )
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful business model canvas coach who gives clear, constructive, and holistic feedback."
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            temperature=0.7
        )

        feedback = response.choices[0].message["content"]
        st.subheader("GPT Feedback")
        st.write(feedback)
