# Hackathon Submission API

## Input / Output Format

**POST** `/api`

```json
// Input
{
  "query": "your question as a string",
  "assets": ["https://url1.com", "https://url2.com"]
}

// Output
{
  "output": "your answer string"
}
```

---

## ⚡ Setup in 3 Minutes

### Step 1 — Install packages
```bash
pip install -r requirements.txt
```

### Step 2 — Add Gemini API key
```bash
copy .env.example .env       # Windows
cp .env.example .env         # Mac/Linux
```
Open `.env` and add:
```
GEMINI_API_KEY=AIzaSyXXXXXXXXXXXX
```
Get free key at: https://aistudio.google.com

### Step 3 — Run the API
```bash
python main.py
```
API runs at: **http://localhost:8000**

### Step 4 — Test it
```bash
python test_api.py
```

---

## API Endpoints

| Method | URL | Description |
|--------|-----|-------------|
| GET | `/` | Check API is running |
| GET | `/health` | Health check |
| POST | `/api` | Main endpoint |
| POST | `/api/query` | Alternative endpoint (same) |

## Swagger Docs
Visit: **http://localhost:8000/docs**

---

## How It Works
1. Receives `query` + list of `asset` URLs
2. Fetches and extracts text from each URL
3. Sends query + content to **Gemini 1.5 Flash** (free)
4. Returns clean answer as `{ "output": "..." }`
