# ClassifAI

A minimal tool for PDF data sensitivity classification using Gemini 2.5 Flash. It analyzes document content and context to apply sensitivity tags (Public, Internal, Confidential, Restricted) without relying on traditional regex patterns.

**Note:** Now supports scan history, stored in Postgres.

### Usage

1. **Set up environment**
Create a `.env` file with your key:
```ini
GEMINI_API_KEY=your_key_here
```

2. **Run with Docker Compose**
```bash
docker-compose up --build
```

The interface will be available at `http://127.0.0.1:8000`.

### Stack

* **Backend:** FastAPI (Python)
* **Model:** Gemini 2.5 Flash
* **Frontend:** HTML/JS (Single file, no frameworks)
* **Database:** PostgreSQL (history of scans)
* **Containerization:** Docker, Docker Compose