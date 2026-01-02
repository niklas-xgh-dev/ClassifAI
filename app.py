import os
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(title="ClassifAI: Sensitivity Engine")

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=FileResponse)
async def home():
    return FileResponse("index.html")

@app.post("/classify")
async def classify_pdf(file: UploadFile = File(...)):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="API Key missing")
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="PDF files only")
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
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
