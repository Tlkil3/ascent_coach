
import streamlit as st
import openai

# Read secrets from .streamlit/secrets.toml
openai.api_key = st.secrets["OPENAI_API_KEY"]
openai.organization = st.secrets["OPENAI_ORG"]
openai.project = st.secrets["OPENAI_PROJECT"]

st.title("Business Model Canvas Coach")
st.subheader("Upload a BMC PDF")

uploaded_file = st.file_uploader("Upload a PDF", type="pdf")
if uploaded_file is not None:
    pdf_bytes = uploaded_file.read()
    try:
        # Placeholder for actual PDF parsing
        extracted_text = "Example extracted text from uploaded BMC PDF."
        st.markdown("### Extracted BMC Text")
        st.write(extracted_text)

        st.markdown("### GPT Feedback")
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a startup coach."},
                {"role": "user", "content": f"Give constructive feedback on this BMC:

{extracted_text}"}
            ],
            temperature=0.7,
        )
        feedback = response.choices[0].message.content
        st.write(feedback)

    except Exception as e:
        st.error(f"Error: {str(e)}")
else:
    st.info("Please upload a PDF to begin.")
