# ClassifAI

A minimal tool for PDF data sensitivity classification using Gemini 2.5 Flash. It analyzes document content and context to apply sensitivity tags (Public, Internal, Confidential, Restricted) without relying on traditional regex patterns.

**Note:** Currently configured to process a single PDF file at a time.

### Usage

1. **Install dependencies**
```bash
pip install fastapi uvicorn python-multipart google-genai python-dotenv

```


2. **Set up environment**
Create a `.env` file with your key:
```ini
GEMINI_API_KEY=your_key_here

```


3. **Run**
```bash
python main.py

```


The interface will be available at `http://127.0.0.1:8000`.

### Stack

* **Backend:** FastAPI (Python)
* **Model:** Gemini 2.5 Flash
* **Frontend:** HTML/JS (Single file, no frameworks)