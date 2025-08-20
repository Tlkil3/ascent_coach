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
    "and holistic feedback."
)

# Streamlit UI
st.title("Business Model Canvas Coach")

uploaded_file = st.file_uploader("Upload a BMC PDF", type="pdf")

if uploaded_file:
    # Load PDF text
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()

    # Display extracted text
    st.subheader("Extracted BMC Text")
    st.text(text[:1000])  # show first 1000 characters for preview

    # Create prompt
    user_prompt = f"""
Please assess the following Business Model Canvas and offer tailored feedback for each of its 12 blocks:
1. Customer Segments
2. Value Propositions
3. Channels
4. Customer Relationships
5. Revenue Streams
6. Key Activities
7. Key Resources
8. Key Partners
9. Cost Structure
10. Kingdom Impact – economic, social, environmental, and spiritual
11. Mission & Vision Alignment
12. Growth Potential

Also highlight any inconsistencies or gaps across the blocks (e.g., a mismatch between the value proposition and the customer segment, or unclear revenue streams).

{text}
"""

    # Query OpenAI
    with st.spinner("Reviewing the canvas..."):
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7
        )
        result = response.choices[0].message.content

    # Show result
    st.subheader("AI Feedback")
    st.write(result)
