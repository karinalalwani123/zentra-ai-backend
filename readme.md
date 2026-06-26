# ⚡ Zentra AI — AI Email Automation Platform

> A production-ready, multi-user AI email assistant that lets you manage Gmail through natural conversation.

---

## 🚀 What is Zentra AI?

Zentra AI is a production-deployed AI email automation platform. Instead of manually managing Gmail, you simply chat with the AI:

```
"read my emails"           → Fetches and classifies your inbox
"draft an email to x@..."  → AI writes a professional email
"send it"                  → Sends via Gmail API
"search gold price today"  → Real-time web search with sources
"what is my name?"         → Remembers your conversation context
```

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 💬 AI Chat | Powered by Groq LLaMA 3.3 70B |
| 📧 Read Emails | Fetch and AI-classify Gmail inbox |
| ✍️ Draft Emails | Generate professional emails via chat |
| 📤 Send Emails | Send directly through Gmail API |
| 🔁 Auto Reply | AI-generated professional replies |
| 🌐 Web Search | Real-time Tavily search (prices, news, weather) |
| 🧠 Memory | Persistent per-user conversation memory |
| 👥 Multi-user | Firebase Auth with isolated data per user |
| 🎙️ Voice Input | Web Speech API integration |
| 👑 Admin Panel | Manage users and roles |

---

## 🏗️ System Architecture

```
                                      ┌──────────────────────┐
                                      │       User           │
                                      └──────────┬───────────┘
                                                 │
                                                 ▼
                              ┌────────────────────────────────┐
                              │ React Frontend (Vercel)        │
                              │ • Chat UI                      │
                              │ • Voice Input                  │
                              │ • Firebase onSnapshot          │
                              │ • Axios API Calls              │
                              └──────────┬─────────────────────┘
                                         │ HTTPS Request
                                         ▼
                              ┌────────────────────────────────┐
                              │ FastAPI Backend (Render)       │
                              │                                │
                              │ POST /chat                     │
                              │ POST /schedule-email           │
                              │ GET /scheduled-emails          │
                              │ GET /ping                      │
                              └──────────┬─────────────────────┘
                                         │
                                         ▼
                     ┌────────────────────────────────────────────┐
                     │       LangGraph StateGraph Workflow        │
                     │                                            │
                     │ 1. Restore State                           │
                     │ 2. Router                                  │
                     │ 3. Add Memory                              │
                     │ 4. Chat                                    │
                     │ 5. Read Email                              │
                     │ 6. Auto Reply                              │
                     │ 7. Send Email                              │
                     │ 8. Cancel Email                            │
                     │ 9. Web Search                              │
                     │10. Validate Draft                          │
                     │11. Validate Email                          │
                     │12. Update Memory                           │
                     │13. Clear Memory                            │
                     │14. Error Handler                           │
                     └──────┬─────────────┬──────────────┬────────┘
                            │             │              │
                            ▼             ▼              ▼
                  ┌──────────────┐ ┌──────────────┐ ┌───────────────┐
                  │ Groq LLM     │ │ Firebase     │ │ Tavily Search │
                  │ LLaMA 3.3 70B│ │ Firestore    │ │ Real-time Web │
                  └──────┬───────┘ └──────┬───────┘ └───────────────┘
                         │                │
                         ▼                ▼
                ┌────────────────┐  ┌──────────────────────┐
                │ Gmail API      │  │ Firebase Collections  │
                │ OAuth2         │  │ users/{uid}/chats     │
                │ Read Emails    │  │ memories/{uid}        │
                │ Send Emails    │  │ pending_emails        │
                │ Reply Emails   │  │ cached_emails         │
                └────────────────┘  │ scheduled_emails      │
                                    └──────────────────────┘
```

---

## 🔗 LangGraph — 14 Workflow Nodes

| Node | Name | Purpose |
|------|------|---------|
| 01 | `restore_state` | Load user's pending email + memory from Firestore |
| 02 | `router` | Keyword-based intent detection |
| 03 | `add_memory` | Save user message to per-user memory |
| 04 | `chat` | Groq LLaMA 3.3 70B response generation |
| 05 | `read_email` | Fetch + classify Gmail inbox |
| 06 | `auto_reply` | Generate professional email reply |
| 07 | `send_email` | Send pending draft via Gmail API |
| 08 | `cancel_email` | Discard pending draft |
| 09 | `web_search` | Real-time Tavily web search |
| 10 | `validate_draft` | Check To/Subject/Body fields |
| 11 | `validate_email` | Regex email format validation |
| 12 | `update_memory` | Persist conversation state |
| 13 | `clear_memory` | Reset context after send |
| 14 | `error_handler` | Catch empty responses gracefully |

---

## 🛠️ Tech Stack

### Backend
- **Python** — Primary language
- **FastAPI** — REST API framework
- **LangGraph** — StateGraph AI workflow (14 nodes)
- **Groq API** — LLaMA 3.3 70B inference
- **Gmail API** — OAuth2 email operations
- **Tavily API** — Real-time web search
- **Firebase Admin SDK** — Firestore + Auth

### Frontend
- **React.js** — Chat interface
- **Tailwind CSS** — Styling
- **Firebase SDK** — Real-time listeners
- **Web Speech API** — Voice input
- **Axios** — HTTP requests

### Infrastructure
- **Vercel** — Frontend deployment
- **Render** — Backend deployment
- **UptimeRobot** — Keep-alive monitoring
- **Firebase Firestore** — Persistent storage
- **GitHub** — CI/CD auto-deploy

---

## 📁 Project Structure

```
zentra-ai-backend/
│
├── api_server.py                          # FastAPI entry point
│
├── src/
│   └── groq_email_agent/
│       ├── agent/
│       │   ├── chat_workflow.py           # LangGraph 14 nodes
│       │   ├── chat.py                    # Groq LLM + prompts
│       │   ├── memory.py                  # Per-user memory
│       │   └── router.py                  # Intent detection
│       │
│       ├── llm/
│       │   └── groq_client.py             # Groq API wrapper
│       │
│       └── tools/
│           ├── gmail_auth.py              # OAuth2 token management
│           ├── gmail_tools.py             # Read/send/reply
│           ├── web_search.py              # Tavily search
│           └── scheduler.py              # Email scheduler
│
└── email-ui/                             # React Frontend
    └── src/
        ├── App.jsx                        # Main component
        ├── firebase.js                    # Firebase config
        ├── hooks/
        │   └── useChat.js                 # Firebase chat hook
        ├── components/
        │   ├── Auth.jsx                   # Login/Register
        │   ├── ChatWindow.jsx             # Chat UI
        │   ├── LeftSidebar.jsx            # Chat history
        │   └── RightSidebar.jsx           # Actions
        └── pages/
            ├── AdminPanel.jsx             # Admin dashboard
            └── ScheduleEmail.jsx          # Scheduler page
```

---

## 🔐 Multi-User Data Isolation

Every piece of data is isolated by Firebase UID:

```
Firebase Firestore:
├── users/{uid}/chats/{chatId}     ← Chat history
├── memories/{uid}                 ← LLM memory (last 10 msgs)
├── pending_emails/{uid}           ← Pending email draft
├── cached_emails/{uid}            ← Gmail inbox cache
└── scheduled_emails/{jobId}       ← Scheduled job queue
```

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
| `GROQ_API_KEY` | Groq API key for LLaMA inference |
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

---

*Built using LangGraph, Groq, Gmail API, Firebase, React, and FastAPI*