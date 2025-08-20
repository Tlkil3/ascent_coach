# BMC Coach – Streamlit App

The **BMC Coach** is a lightweight, browser-accessible AI agent designed to help founders evaluate and strengthen their Business Model Canvas (BMC). It is particularly suited for accelerator programs, early-stage entrepreneurs, and distributed coaching environments like those supported by Sinapis.

---

## 🌐 How It's Used

This app is deployed **remotely** (e.g. via [Streamlit Cloud](https://streamlit.io/cloud)) so users can upload a BMC PDF and receive coaching feedback without installing anything locally.

---

## 🧠 Features

- Extracts text from a user-uploaded BMC PDF
- Analyzes using OpenAI GPT (via API key)
- Provides clear, constructive feedback per BMC box
- Specialized prompt system supports Sinapis' values, including Kingdom Impact

---

## 🔐 Configuration (via Streamlit Secrets)

You **must** supply these keys in `.streamlit/secrets.toml` (or through the Streamlit web UI if deployed):

```toml
OPENAI_API_KEY = "sk-proj-..."
OPENAI_ORG = "org-..."
OPENAI_PROJECT = "Default project"
```

---

## 📁 Key Files

- `app.py`: Main Streamlit interface and logic
- `secrets.toml`: Store OpenAI credentials locally (or use Streamlit UI)
- `README.md`: This file

---

## 🧑‍💼 Administrator Setup Steps

1. Fork or clone this repo.
2. Add your OpenAI credentials via `.streamlit/secrets.toml` or the Streamlit UI.
3. Deploy using [Streamlit Cloud](https://streamlit.io/cloud).
4. Share the public app link with your team.

---

## ✍️ Attribution

This tool was developed by the Sinapis team and integrates their unique framework for entrepreneur development.