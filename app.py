
import streamlit as st
import fitz  # PyMuPDF
import openai
import tempfile

# Load OpenAI API key from Streamlit secrets
openai.api_key = st.secrets["OPENAI_API_KEY"]

st.set_page_config(page_title="Business Model Canvas Coach", layout="centered")
st.title("📊 Business Model Canvas Coach")

st.markdown("### Upload a BMC PDF")
uploaded_file = st.file_uploader("Upload a BMC PDF", type="pdf")

if uploaded_file is not None:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(uploaded_file.read())
        tmp_file_path = tmp_file.name

    doc = fitz.open(tmp_file_path)
    bmc_text = ""
    for page in doc:
        bmc_text += page.get_text()

    st.markdown("### Extracted BMC Text")
    st.text(bmc_text)

    if st.button("Assess BMC"):
        with st.spinner("Thinking..."):
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are a startup coach assessing a business model canvas (BMC). Provide concise, practical, and holistic feedback."},
                        {"role": "user", "content": f"""Give constructive feedback on this BMC:

{bmc_text}

Highlight strengths and weaknesses in each of the 9 blocks: Customer Segments, Value Propositions, Channels, Customer Relationships, Revenue Streams, Key Activities, Key Resources, Key Partnerships, and Cost Structure.

Also highlight any inconsistencies or gaps across the blocks—for example, a mismatch between the value proposition and the customer segment, or unclear revenue streams.

This box reflects the founder's intended faith-driven or missional impact in the world. Please assess their intentions across four areas:

1. Is the mission clearly articulated?
2. Is it meaningfully integrated into the business model?
3. Are there potential tensions between the mission and the model?
4. What suggestions do you have to improve alignment or impact?

Conclude with 3 coaching questions to push the founder's thinking forward."""}
                    ],
                    temperature=0.7,
                )
                st.markdown("### AI Feedback")
                st.write(response.choices[0].message.content.strip())
            except Exception as e:
                st.error(f"Error generating feedback: {e}")
