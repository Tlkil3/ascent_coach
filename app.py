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
SYSTEM_PROMPT = """
You are a strategic business model coach reviewing Business Model Canvases (BMCs) for entrepreneurs. The BMC includes 12 blocks:

1. Customer Segments  
2. Value Proposition  
3. Channels  
4. Customer Relationships  
5. Revenue Streams  
6. Key Activities  
7. Key Resources  
8. Key Partners  
9. Cost Structure  
10. Kingdom Impact  
11. Mission  
12. Vision  

For each of the 12 blocks, perform the following:
- **Identify** and briefly summarize the founder's content.
- **Evaluate** the strength and clarity of what's been provided.
- **Ask 1–3 powerful, probing questions** to help the founder strengthen that section.

Use clear and constructive feedback. Write in a tone that is encouraging but direct.

**Special instructions for Kingdom Impact:**
This box reflects the founder’s intended faith-driven or missional impact in the world. Please assess their intentions across four areas:
- Economic (e.g., job creation, income growth, economic opportunity)
- Social (e.g., clean water, education, health, community)
- Environmental (e.g., waste reduction, sustainability)
- Spiritual (e.g., Bible study, chaplaincy, ethical culture, giving)

If missing or unclear, suggest how the founder might articulate Kingdom Impact more intentionally.
"""


Also highlight any inconsistencies or gaps across the blocks—e.g., a mismatch between the value proposition and the customer segment, or unclear revenue streams.

Close your feedback with a brief summary of strengths and suggested refinements.
"""
    try:
        response = openai.ChatCompletion.create(
    model="gpt-4o",  # ✅ Use the latest GPT-4 Omni model if available
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": full_prompt},
    ],
    temperature=0.7,
    max_tokens=1500
)

        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"\n\n❌ Error: {e}"

# --- Streamlit UI ---
st.set_page_config(page_title="Sinapis BMC Refiner", layout="wide")
st.title("📊 BMC Coach for Sinapis Founders")

st.markdown("""
Upload a PDF of your Business Model Canvas, then describe your business so we can give you tailored feedback.
""")

uploaded_file = st.file_uploader("Upload your BMC as a PDF", type="pdf")
overview = st.text_area("Briefly describe your business:", placeholder="What does your business do? Who are your customers? What's your vision?")

if st.button("Analyze Canvas"):
    if uploaded_file and overview:
        with st.spinner("Analyzing your BMC..."):
            bmc_text = extract_pdf_text(uploaded_file)
            result = review_canvas(bmc_text, overview)
            st.markdown("---")
            st.subheader("🧐 AI Feedback")
            st.write(result)
    else:
        st.error("Please upload a PDF and provide a business overview.")