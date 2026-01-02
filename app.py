import os
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from google import genai
from google.genai import types
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime

# --- Database setup ---
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/classifai")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class ScanResult(Base):
    __tablename__ = "scan_results"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(256))
    result = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

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
        # Save result to DB
        db = SessionLocal()
        scan = ScanResult(filename=file.filename, result=response.text)
        db.add(scan)
        db.commit()
        db.refresh(scan)
        db.close()
        return {"result": response.text}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Engine Error")

@app.get("/history")
async def get_history():
    try:
        db = SessionLocal()
        scans = db.query(ScanResult).order_by(ScanResult.created_at.desc()).limit(20).all()
        db.close()
        return [
            {
                "id": scan.id,
                "filename": scan.filename,
                "created_at": scan.created_at.isoformat(),
                "result": scan.result
            }
            for scan in scans
        ]
    except SQLAlchemyError as e:
        print(e)
        raise HTTPException(status_code=500, detail="DB Error")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
