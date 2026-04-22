# main.py — Hackathon Submission API
# Input:  { "query": "question", "assets": ["url1", "url2"] }
# Output: { "output": "answer string" }

import os
import logging
import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("hackathon_api")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

app = FastAPI(title="Hackathon API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class QueryRequest(BaseModel):
    query: str
    assets: Optional[List[str]] = []

class QueryResponse(BaseModel):
    output: str


def fetch_url_content(url: str, max_words: int = 800) -> str:
    try:
        jina_url = f"https://r.jina.ai/{url}"
        resp = requests.get(jina_url, timeout=10, headers={"Accept": "text/plain"})
        if resp.status_code == 200 and len(resp.text) > 100:
            return " ".join(resp.text.split()[:max_words])
    except Exception:
        pass
    try:
        resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            for tag in soup(["script","style","nav","footer","header","aside"]):
                tag.decompose()
            return " ".join(soup.get_text(separator=" ", strip=True).split()[:max_words])
    except Exception as e:
        logger.error(f"Failed to fetch {url}: {e}")
    return f"[Could not fetch content from {url}]"


def answer_with_gemini(query: str, context: str) -> str:
    model = genai.GenerativeModel(
        "gemini-2.0-flash",
        generation_config=genai.types.GenerationConfig(temperature=0.1),
    )

    if context.strip():
        prompt = f"""You are a precise question-answering assistant.

Use the following source content to answer the question accurately.

SOURCE CONTENT:
{context}

QUESTION:
{query}

Instructions:
- Answer in a clean, complete sentence
- Be direct and concise
- Match the style: if the question is "What is 10 + 15?", answer "The sum is 25."
- Do NOT add preamble like "Based on the sources..." or "According to..."
- Just answer directly in one or two sentences"""
    else:
        prompt = f"""Answer this question in a clean, complete sentence.

QUESTION: {query}

Instructions:
- Be direct and concise
- Answer in a full sentence
- Example: "What is 10 + 15?" → "The sum is 25."
- Do NOT add preamble or explanation, just the answer"""

    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        logger.error(f"Gemini error: {e}")
        try:
            fallback = genai.GenerativeModel("gemini-2.0-flash")
            return fallback.generate_content(prompt).text.strip()
        except Exception as e2:
            raise HTTPException(status_code=500, detail=f"Gemini API error: {str(e2)}")


@app.get("/")
def root():
    return {"status": "running", "message": "Hackathon API is live!", "endpoint": "POST /v1/answer"}

@app.get("/health")
def health():
    return {"status": "ok", "gemini_configured": bool(GEMINI_API_KEY)}


# ── MAIN ENDPOINT — matches hackathon format ──
@app.post("/v1/answer", response_model=QueryResponse)
def answer(request: QueryRequest):
    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="query cannot be empty")

    logger.info(f"Query: {request.query[:100]}")
    logger.info(f"Assets: {len(request.assets or [])} URLs")

    context_parts = []
    for i, url in enumerate(request.assets or []):
        if url and url.startswith("http"):
            logger.info(f"Fetching asset {i+1}: {url[:60]}")
            content = fetch_url_content(url)
            context_parts.append(f"--- Source {i+1}: {url} ---\n{content}")

    context = "\n\n".join(context_parts)
    answer_text = answer_with_gemini(request.query, context)
    logger.info(f"Answer: {answer_text[:100]}")
    return QueryResponse(output=answer_text)


# Also support /api for backwards compat
@app.post("/api", response_model=QueryResponse)
def answer_api(request: QueryRequest):
    return answer(request)


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
