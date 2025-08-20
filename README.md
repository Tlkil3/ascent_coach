# Ascent Coach – Business Model Canvas Assessment Tool

Ascent Coach is a Streamlit-based AI assistant designed to help entrepreneurs of smaller,  growth-oriented businesses and coaches assess and strengthen their businesses.  This tool is focused on assessing business model canvases. Powered by GPT-4, it provides structured feedback and tailored improvement suggestions across 12 standard canvas blocks, plus an additional **Kingdom Impact** block reflecting Sinapis’ faith-driven values.

---

## 🧠 Purpose

This tool supports early-stage founders—especially those in Kenya and similar frontier markets—in improving clarity, completeness, and strategic thought in their business models. These businesses have gotten taction, are post-revenue but are in the stage where there is risk of losing momentum (they are in the $500k-$2M in annual revenue category).  It also helps Sinapis coaches and staff scale their review capacity.

---

## 🧩 How It Works

1. **User uploads a `.docx` input file** with clearly labeled sections:
   - Business Name  
   - Business Description  
   - Sections 1–12 of the Business Model Canvas  
   - Section 13: Kingdom Impact

2. The app **parses each section**, sends targeted prompts to GPT-4, and receives coaching feedback.

3. Feedback is **organized into a well-formatted Word document**, mirroring the canvas structure:
   - Each section includes:
     - Summary of strengths
     - Suggested improvements
     - Tailored probing questions
   - A final summary synthesizes cross-cutting insights

4. The output file is named using the **business name** and can be downloaded directly from the app.

---

## 🛠️ Requirements

Install dependencies from the `requirements.txt` file:

```bash
pip install -r requirements.txt
```

Note: If deploying locally and not using Streamlit Cloud’s built-in secrets manager, you will also need a `.env` or `secrets.toml` file with your OpenAI credentials.

---

## 🚀 Deployment

### 🟢 Option A: Local (for testing)

1. Clone the repo:
   ```bash
   git clone https://github.com/<your-org>/AscentCoach.git
   cd AscentCoach
   ```

2. Launch:
   ```bash
   streamlit run app.py
   ```

### 🟣 Option B: Streamlit Cloud

1. Push the repo to GitHub
2. Create a new app in [Streamlit Cloud](https://streamlit.io/cloud)
3. In the **App Settings → Secrets**, paste:

```toml
OPENAI_API_KEY = "sk-proj-..."
OPENAI_PROJECT = "your_project_name"
```

4. Deploy. The app will be available for remote team use immediately.

---

## 🧾 File Structure

```
AscentCoach/
│
├── app.py                   # Main Streamlit app
├── requirements.txt         # Python dependencies
├── README.md                # You're reading it!
└── sample_input.docx        # Optional example input (for testing)
```

---

## 🙏 Kingdom Impact Block

This additional section evaluates the intentional spiritual, social, environmental, and economic impact of the business. It reflects Sinapis’ values and is treated with the same structured feedback process as other canvas blocks.

---

## 📬 Feedback and Support

For issues, reach out to [tkilgore@sinapis.org](mailto:tkilgore@sinapis.org) or open an issue in this repository.

---

© 2025 Sinapis Group. All rights reserved.