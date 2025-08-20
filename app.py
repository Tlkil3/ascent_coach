
import openai
import streamlit as st
import os
import fitz  # PyMuPDF

# Set OpenAI credentials
openai.api_key = st.secrets["OPENAI_API_KEY"]
openai.organization = st.secrets["OPENAI_ORG"]
openai.project = st.secrets["OPENAI_PROJECT"]

# Optionally show a partial key for debugging
st.write("API Key loaded:", openai.api_key[:5] + "..." + openai.api_key[-4:])
print("API key found:", openai.api_key)
print("Loaded key:", openai.api_key[:6])

# System instruction for the AI agent
SYSTEM_PROMPT = (
    "You are a coach reviewing Business Model Canvases for smaller, higher-growth businesses in Nairobi, Kenya. "
    "You work with Sinapis, a faith-driven accelerator that supports entrepreneurs in integrating spiritual, social, "
    "environmental, and economic impact into their business models. You aim to give founders clear, constructive, "
    "and holistic feedback.
"
    "For each of the 12 boxes of the canvas, assess strengths and weaknesses, and generate thoughtful follow-up "
    "questions to help the founder refine and strengthen their thinking. Include:
"
    "- Clarity and completeness of each box
"
    "- Strategic alignment with mission and growth
"
    "- Impact potential (especially Kingdom Impact)
"
    "Also highlight any inconsistencies or gaps across the blocks (e.g., a mismatch between the value proposition and "
    "the customer segment, or unclear revenue streams).
"
    "Use a tone that is encouraging, constructive, and precise."
)

# Example user input (from PDF or manual entry)
user_input = st.text_area("Paste the BMC content here (or upload a file):")

if user_input:
    st.write("Processing your BMC...")
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_input},
        ]
    )
    st.markdown("### Feedback")
    st.write(response['choices'][0]['message']['content'])
