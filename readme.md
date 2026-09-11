
---

## ⚡ Real Engineering Challenges Solved

**1. Token Limit Error (48,118 vs 12,000 tokens)**
- Hit 413 error requesting too many tokens
- Fixed by truncating search results to 500 chars
- Limited memory to last 10 messages per user

**2. Multi-User Memory Bleed**
- Single global memory list caused data leaks
- Fixed by keying `CHAT_MEMORIES` dict by Firebase UID
- Tested with two simultaneous accounts successfully

**3. Gmail OAuth Token Expiry**
- Tokens expired mid-deployment on Render
- Fixed by storing token as `GMAIL_TOKEN_BASE64` env var
- Added auto-refresh logic for seamless operation

**4. Scheduler Duplicate Sends (21 times!)**
- Render sleep cycles killed Python threads
- Fixed with atomic status claiming in Firestore
- Status: `pending → sending → sent` prevents duplicates

**5. Firebase Security Incident**
- Accidentally exposed service account key on GitHub
- Immediately revoked, generated new key
- Migrated to environment variables on Render

**6. Deprecated Groq Model**
- `llama-3.3-70b-versatile` was deprecated by Groq
- Migrated to `openai/gpt-oss-120b` (Sept 2026)

---

## 🚀 Local Setup

### Prerequisites
```bash
Python 3.11+
Node.js 18+
```

### Backend Setup
```bash
# Clone repo
git clone https://github.com/karinalalwani123/zentra-ai-backend
cd zentra-ai-backend

# Create .env file
GROQ_API_KEY=your_groq_key
TAVILY_API_KEY=your_tavily_key

# Place these files:
# serviceAccountKey.json (Firebase Admin)
# src/groq_email_agent/tools/credentials.json (Gmail OAuth)
# src/groq_email_agent/tools/token.pickle (Gmail token)

# Run backend
python -m uvicorn api_server:app --reload
```

### Frontend Setup
```bash
cd email-ui

# Create .env file
REACT_APP_FIREBASE_API_KEY=your_key
REACT_APP_FIREBASE_AUTH_DOMAIN=your_domain
REACT_APP_FIREBASE_PROJECT_ID=your_project
REACT_APP_FIREBASE_STORAGE_BUCKET=your_bucket
REACT_APP_FIREBASE_MESSAGING_SENDER_ID=your_id
REACT_APP_FIREBASE_APP_ID=your_app_id
REACT_APP_API_URL=http://127.0.0.1:8000

# Run frontend
npm install
npm start
```

---

## 🌐 Environment Variables (Render)

| Variable | Description |
|----------|-------------|
| `GROQ_API_KEY` | Groq API key for gpt-oss-120b inference |
| `TAVILY_API_KEY` | Tavily API key for web search |
| `FIREBASE_CREDENTIALS_JSON` | Firebase service account JSON |
| `GMAIL_TOKEN_BASE64` | Gmail OAuth token (base64 encoded) |

---

## 📊 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/chat` | Main AI chat endpoint |
| `GET` | `/ping` | Health check + restore scheduled jobs |
| `POST` | `/schedule-email` | Schedule email for future delivery |
| `GET` | `/scheduled-emails` | Get user's scheduled jobs |
| `POST` | `/send-email` | Send email via Gmail API |

---

## 🎯 Known Limitations

- **Single Gmail account** — All users share one OAuth token
- **Groq free tier** — Limited tokens per minute
- **Render free tier** — Server sleeps after 15 mins inactivity
- **Scheduler delay** — Max 5 min delay due to UptimeRobot ping interval

---

## 🗺️ Roadmap

- [ ] Per-user Gmail OAuth (each user connects their own Gmail)
- [ ] Upgrade to paid LLM tier for higher limits
- [ ] Celery + Redis for reliable email scheduling
- [ ] Docker containerization
- [ ] Unit and integration tests

---

## 👩‍💻 Built By

**Karina Lalwani**
- 📧 kareenalalwani123@gmail.com
- 💼 [LinkedIn](https://linkedin.com/in/karina-lalwani-803b11271)
- 🐙 [GitHub](https://github.com/karinalalwani123)

---

*Built using LangGraph, Groq, Gmail API, Firebase, React, and FastAPI*