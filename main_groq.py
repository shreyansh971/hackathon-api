# main_groq.py — Uses Groq (free, fast) + Gemini fallback
import os, logging, requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

app = FastAPI(title="Hackathon API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class QueryRequest(BaseModel):
    query: str
    assets: Optional[List[str]] = []

class QueryResponse(BaseModel):
    output: str

def fetch_url(url, max_words=800):
    try:
        r = requests.get(f"https://r.jina.ai/{url}", timeout=10, headers={"Accept": "text/plain"})
        if r.status_code == 200 and len(r.text) > 100:
            return " ".join(r.text.split()[:max_words])
    except: pass
    try:
        r = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(r.text, "html.parser")
        for t in soup(["script","style","nav","footer"]): t.decompose()
        return " ".join(soup.get_text(" ", strip=True).split()[:max_words])
    except: return ""

def make_prompt(query, context):
    if context:
        return f"Use these sources to answer.\n\nSOURCES:\n{context}\n\nQUESTION: {query}\n\nAnswer in one complete sentence. No preamble. Example: 'What is 10+15?' -> 'The sum is 25.'"
    return f"Answer in one complete sentence. No preamble.\n\nQUESTION: {query}\n\nExample: 'What is 10+15?' -> 'The sum is 25.'"

def groq_answer(prompt):
    r = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
        json={"model": "llama-3.1-8b-instant", "messages": [{"role":"user","content":prompt}], "temperature":0.1, "max_tokens":300},
        timeout=20
    )
    if r.status_code != 200: raise Exception(f"Groq {r.status_code}: {r.text[:200]}")
    return r.json()["choices"][0]["message"]["content"].strip()

def gemini_answer(prompt):
    import google.generativeai as genai
    genai.configure(api_key=GEMINI_API_KEY)
    for m in ["gemini-2.0-flash","gemini-2.0-flash-lite","gemini-1.5-flash-latest"]:
        try:
            return genai.GenerativeModel(m).generate_content(prompt).text.strip()
        except Exception as e:
            logger.warning(f"{m} failed: {e}")
    raise HTTPException(500, "All Gemini models failed. Try getting a new API key from aistudio.google.com")

@app.get("/")
def root(): return {"status": "running", "endpoint": "POST /v1/answer"}

@app.get("/health")
def health(): return {"status": "ok", "groq": bool(GROQ_API_KEY), "gemini": bool(GEMINI_API_KEY)}

@app.post("/v1/answer", response_model=QueryResponse)
def answer(req: QueryRequest):
    if not req.query.strip(): raise HTTPException(400, "query is empty")
    ctx = "\n\n".join(f"[Source {i+1}] {fetch_url(u)}" for i,u in enumerate(req.assets or []) if u.startswith("http"))
    prompt = make_prompt(req.query, ctx)
    if GROQ_API_KEY:
        try: return QueryResponse(output=groq_answer(prompt))
        except Exception as e: logger.warning(f"Groq failed: {e}")
    if GEMINI_API_KEY:
        return QueryResponse(output=gemini_answer(prompt))
    raise HTTPException(500, "No API key set in .env file")

@app.post("/api", response_model=QueryResponse)
def answer_api(req: QueryRequest): return answer(req)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main_groq:app", host="0.0.0.0", port=int(os.getenv("PORT",8000)), reload=False)
