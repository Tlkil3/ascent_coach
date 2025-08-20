
    import streamlit as st
    import fitz  # PyMuPDF
    import openai

    # Initialize OpenAI client
    client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

    st.title("Business Model Canvas Coach")
    st.subheader("Upload a BMC PDF")

    uploaded_file = st.file_uploader("Upload a BMC PDF", type=["pdf"])

    if uploaded_file is not None:
        with fitz.open(stream=uploaded_file.read(), filetype="pdf") as doc:
            text = ""
            for page in doc:
                text += page.get_text()

        st.subheader("Extracted BMC Text")
        st.write(text)

        if st.button("Get Feedback"):
            with st.spinner("Analyzing your BMC..."):
                messages = [
                    {
                        "role": "user",
                        "content": f"""Give constructive feedback on this BMC:

{text}

Highlight areas of strength, weakness, and opportunities for improvement. Be specific and clear. 
Also highlight any inconsistencies or gaps across the blocks (e.g., a mismatch between the value proposition and the customer segment, or unclear revenue streams)."""
                    }
                ]

                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=messages,
                    temperature=0.7,
                )
                st.subheader("AI Feedback")
                st.write(response.choices[0].message.content)
