import os
import uvicorn
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(title="ClassifAI: Sensitivity Engine")

# --- FRONTEND ---
html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ClassifAI</title>
    <style>
        :root {
            --bg: #f5f5f7; /* Apple System Gray 6 */
            --card-bg: #ffffff;
            --text-primary: #1d1d1f;
            --text-secondary: #86868b;
            --accent: #0071e3; /* Apple Blue */
            --radius: 20px;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Helvetica Neue", sans-serif;
            background-color: var(--bg);
            color: var(--text-primary);
            margin: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            -webkit-font-smoothing: antialiased;
        }

        .main-card {
            width: 100%;
            max-width: 720px;
            background: var(--card-bg);
            border-radius: var(--radius);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.04);
            padding: 60px;
            transition: transform 0.3s ease;
        }

        /* Typography */
        h1 {
            font-size: 40px;
            font-weight: 600;
            letter-spacing: -0.02em;
            margin: 0 0 10px 0;
            text-align: center;
        }

        p.subtitle {
            font-size: 19px;
            font-weight: 400;
            color: var(--text-secondary);
            text-align: center;
            margin: 0 0 50px 0;
            line-height: 1.4;
        }

        /* Upload Zone - Minimalist */
        .upload-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 20px;
        }

        .file-display {
            font-size: 15px;
            color: var(--text-secondary);
            height: 20px;
            font-weight: 500;
        }

        /* Buttons: Pill Shaped */
        .btn {
            background-color: #1d1d1f; /* Almost Black */
            color: white;
            border: none;
            padding: 16px 36px;
            font-size: 17px;
            border-radius: 999px; /* Pill shape */
            cursor: pointer;
            font-weight: 500;
            transition: all 0.2s ease;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        
        .btn:hover {
            transform: scale(1.02);
            background-color: #333;
        }
        
        .btn:disabled {
            background-color: #d2d2d7;
            color: #86868b;
            transform: none;
            box-shadow: none;
            cursor: default;
        }

        .secondary-btn {
            background: transparent;
            color: var(--accent);
            padding: 10px 20px;
            font-size: 15px;
            box-shadow: none;
        }
        .secondary-btn:hover {
            background: transparent;
            text-decoration: underline;
            transform: none;
        }

        /* Result Area */
        #result-container {
            margin-top: 50px;
            padding-top: 40px;
            border-top: 1px solid #d2d2d7;
            display: none;
            animation: fadeIn 0.6s ease-out;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        /* Markdown Styling - Clean */
        .markdown-content h3 {
            font-size: 13px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-secondary);
            margin-top: 30px;
            margin-bottom: 10px;
            font-weight: 600;
        }

        .markdown-content p {
            font-size: 17px;
            line-height: 1.5;
            color: var(--text-primary);
            margin-bottom: 15px;
        }

        .markdown-content strong {
            font-weight: 600;
            color: var(--text-primary);
        }

        .markdown-content ul {
            padding-left: 20px;
            margin: 0;
        }
        
        .markdown-content li {
            margin-bottom: 8px;
            font-size: 17px;
            color: var(--text-primary);
        }

        /* Loading State */
        .spinner {
            display: none;
            width: 24px;
            height: 24px;
            border: 3px solid #d2d2d7;
            border-radius: 50%;
            border-top-color: #1d1d1f;
            animation: spin 1s linear infinite;
            margin: 20px auto;
        }

        @keyframes spin { to { transform: rotate(360deg); } }

    </style>
</head>
<body>

    <div class="main-card">
        <h1>ClassifAI</h1>
        <p class="subtitle">Automated Data Sensitivity Classification.</p>

        <div class="upload-container">
            <button class="secondary-btn" onclick="document.getElementById('file-input').click()">Choose PDF Document</button>
            <input type="file" id="file-input" accept="application/pdf" hidden onchange="handleFileSelect()">
            
            <div id="file-name" class="file-display"></div>
            
            <button id="action-btn" class="btn" onclick="classify()" disabled>Analyze Sensitivity</button>
        </div>

        <div id="loader" class="spinner"></div>

        <div id="result-container">
            <div id="markdown-output" class="markdown-content"></div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <script>
        function handleFileSelect() {
            const fileInput = document.getElementById('file-input');
            const fileName = document.getElementById('file-name');
            const btn = document.getElementById('action-btn');
            
            if (fileInput.files.length > 0) {
                fileName.innerText = fileInput.files[0].name;
                btn.disabled = false;
                // Clear previous results
                document.getElementById('result-container').style.display = 'none';
            }
        }

        async function classify() {
            const fileInput = document.getElementById('file-input');
            const btn = document.getElementById('action-btn');
            const loader = document.getElementById('loader');
            const resultContainer = document.getElementById('result-container');
            const output = document.getElementById('markdown-output');

            btn.disabled = true;
            btn.style.opacity = "0.5";
            loader.style.display = 'block';
            resultContainer.style.display = 'none';

            const formData = new FormData();
            formData.append("file", fileInput.files[0]);

            try {
                const response = await fetch("/classify", {
                    method: "POST",
                    body: formData
                });

                if (!response.ok) throw new Error("Analysis failed");

                const data = await response.json();
                
                output.innerHTML = marked.parse(data.result);
                loader.style.display = 'none';
                resultContainer.style.display = 'block';

            } catch (e) {
                alert("Error: " + e.message);
                loader.style.display = 'none';
            } finally {
                btn.disabled = false;
                btn.style.opacity = "1";
            }
        }
    </script>
</body>
</html>
"""

# --- BACKEND LOGIC ---

@app.get("/", response_class=HTMLResponse)
async def home():
    return html_content

@app.post("/classify")
async def classify_pdf(file: UploadFile = File(...)):
    # 1. Check API Key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="API Key missing")

    # 2. Check File Type
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="PDF files only")

    # 3. Process with Gemini
    try:
        client = genai.Client(api_key=api_key)
        pdf_bytes = await file.read()

        prompt = """
        Analyze this document for data sensitivity.
        Return the result in clean Markdown. No intro, no conversational filler.

        Format:
        
        ### Sensitivity Level
        **[Choose: Public / Internal / Confidential / Restricted]**
        
        ### Summary
        (One clear sentence describing the document nature)

        ### Key Data Detected
        (Bullet points of specific data elements found, e.g., Financial Projections, Customer Emails, Source Code)

        ### Reasoning
        (Brief explanation of why this level was chosen)
        """

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf"),
                prompt
            ]
        )

        return {"result": response.text}

    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Engine Error")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)