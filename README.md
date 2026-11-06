# ContractIQ

Upload a contract and get back a plain-English review: an executive summary, a 0–100 risk score, every important clause rated low / medium / high with the reason, the obligations you're signing up for (with due dates), and alerts for the parts that need attention before you sign.

**Live:** [contractiq-ten.vercel.app](https://contractiq-ten.vercel.app)

| | |
|---|---|
| **Frontend** | Next.js 16 (App Router), React 19, TanStack Query, Tailwind CSS 4 — deployed on Vercel |
| **Backend** | FastAPI, async SQLAlchemy 2, JWT auth — deployed on Render |
| **Database** | SQLite locally, PostgreSQL in production (uploaded files are stored in the database, so redeploys don't lose them) |
| **AI** | Ollama Cloud (`gpt-oss:20b`) by default, with Gemini and OpenAI as automatic fallbacks |

## How it works

```
upload (.pdf / .docx / .txt)
  ─► text extraction ─► scanned PDF? ─► OCR with Gemini
  ─► parser agent      contract type, parties, dates
  ─► risk agent        is this actually a contract?  no ─► stop, say what it is
                       yes ─► summary, risk score, clause-by-clause risk, recommendations
  ─► obligation agent  who must do what, by when, priority
  ─► saved ─► obligations list + alerts (high-risk clauses, high-priority obligations)
```

Analysis runs in the background after upload; the contract shows as *processing* until it finishes or fails.

- **Not-a-contract check.** Invoices, resumes, articles and lorem-ipsum text are recognised and reported as what they are, instead of being forced into a fake risk review.
- **Scanned PDFs.** If a PDF has under 100 characters of text, it's sent to Gemini for OCR (needs `GEMINI_API_KEY`). Password-protected PDFs and legacy `.doc` files are rejected with a clear message.
- **Provider fallback.** The provider in `LLM_PROVIDER` is tried first, then every other configured provider in the order Ollama → Gemini → OpenAI. If all of them fail, the analysis is marked failed and you can re-run it. The mock provider is only used when you explicitly set `LLM_PROVIDER=mock` — it is never used to fill in for a failed real provider, so you never see made-up results.

## Features

- **Dashboard** — contract counts, risk distribution, open obligations, unread alerts
- **Contract review** — summary, risk bar, key dates, parties, clause cards with risk level and explanation, negotiation recommendations
- **Obligations** — extracted automatically; filter, edit, mark complete
- **Alerts** — created for high-risk clauses and high-priority obligations; mark read / read all
- **Re-analyse** any contract (e.g. after configuring a better model)
- **Accounts** — register / login with JWT; each user sees only their own contracts

## Run locally

Needs Python 3.10+ and Node 20+.

**Backend** (http://localhost:8000, API docs at `/docs`)

```bash
git clone https://github.com/Abhinav-836/contractiq.git
cd contractiq/backend
python -m venv venv
venv\Scripts\activate                # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt

cp ../.env.example .env              # Windows: copy ..\.env.example .env
python main.py
```

The example config uses `LLM_PROVIDER=mock`, so you can click through the whole app without any API key. For real analysis, set a provider and its key (see below).

**Frontend** (http://localhost:5173)

```bash
cd contractiq/frontend
npm install
echo NEXT_PUBLIC_API_URL=http://localhost:8000 > .env.local
npm run dev
```

## Configuration

Backend settings are read from `backend/.env` (template: `.env.example`).

| Variable | Default | Notes |
|---|---|---|
| `LLM_PROVIDER` | `ollama` | `ollama`, `gemini`, `openai` or `mock` |
| `OLLAMA_BASE_URL` / `OLLAMA_MODEL` | `https://ollama.com` / `gpt-oss:20b` | Use `http://localhost:11434` and `OLLAMA_IS_CLOUD=false` for a local Ollama |
| `OLLAMA_API_KEY` | — | Required for Ollama Cloud |
| `GEMINI_API_KEY` / `GEMINI_MODEL` | — / `gemini-1.5-flash` | Also enables OCR for scanned PDFs |
| `OPENAI_API_KEY` / `OPENAI_MODEL` | — / `gpt-4o-mini` | |
| `DATABASE_URL` | `sqlite+aiosqlite:///./contractiq.db` | Production: `postgresql+asyncpg://user:pass@host/db` |
| `ALLOWED_ORIGINS` | `http://localhost:3000,http://localhost:5173` | Comma-separated frontend URLs (trailing slashes are stripped) |
| `MAX_FILE_SIZE_MB` | `20` | |
| `SECRET_KEY`, `JWT_SECRET` | dev values | **Must** be changed when `APP_ENV=production` — the server refuses to start otherwise |
| `SEED_DEV_USER` | `false` | `true` creates `test@example.com` / `test1234` on an empty database (local only) |

Frontend: `NEXT_PUBLIC_API_URL` — the backend URL, no trailing slash.

## API

All routes are under `/api/v1`; everything except register/login needs a `Bearer` token. Full interactive docs at `/docs`.

| Area | Endpoints |
|---|---|
| Auth | `POST /auth/register`, `POST /auth/login`, `GET /auth/me` |
| Contracts | `GET /contracts`, `GET /contracts/stats`, `POST /contracts/upload`, `GET /contracts/{id}`, `POST /contracts/{id}/analyze`, `DELETE /contracts/{id}` |
| Analysis | `GET /analysis/contract/{contract_id}`, `GET /analysis/{id}` |
| Obligations | `GET /obligations`, `GET /obligations/stats`, `GET/PATCH/DELETE /obligations/{id}`, `PATCH /obligations/{id}/complete` |
| Alerts | `GET /alerts`, `GET /alerts/stats`, `PATCH /alerts/{id}/read`, `POST /alerts/mark-all-read`, `DELETE /alerts/{id}` |
| Status | `GET /health`, `GET /api/v1/llm/status` (active provider and fallback chain) |

## Project structure

```
backend/
  apps/api/        FastAPI app, routes, startup
  modules/         users, contracts, analysis, obligations, alerts (api / service / repository / models)
  ai/agents/       parser → risk → obligation pipeline
  ai/llm/          Ollama, Gemini, OpenAI, mock clients + provider router
  ai/prompts/      risk analysis prompt (risk.yaml)
  ingestion/       PDF / DOCX / TXT extraction, Gemini OCR
  core/            config, security, logging
frontend/
  app/             Next.js routes: dashboard, contracts, upload, obligations, alerts, login, register
  components/      clause review, risk bar, contract table, auth form
  lib/             API client, queries, session
```

## Limitations

- Only the first ~15,000 characters of a contract are sent to the model, so very long agreements are reviewed on their opening sections.
- Analysis runs as a background task inside the API process, not a separate worker queue. If the server restarts mid-analysis (common on Render's free tier), that contract is marked failed on startup and needs a re-analyse.
- This is an AI review to speed up reading a contract, not legal advice.

---

Built by **Abhinav Ashutosh** · [GitHub](https://github.com/Abhinav-836)