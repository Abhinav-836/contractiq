# ContractIQ - AI-Powered Contract Intelligence Platform

ContractIQ is an enterprise-grade AI-powered contract analysis platform that automatically extracts, analyzes, and visualizes key information from legal documents using multiple LLM providers with intelligent fallback chains.

## 🎯 What It Does

- **Upload any contract** (PDF, DOC, DOCX, TXT) and get instant AI-powered analysis
- **Extract key clauses** with risk assessments (high/medium/low)
- **Identify obligations** with due dates and priority levels
- **Generate actionable recommendations** for contract negotiation
- **Create automatic alerts** for high-risk items and upcoming deadlines
- **Track all contracts** in one dashboard with real-time status updates

## 🏗️ Tech Stack

### Backend
| Technology | Version | Purpose |
|------------|---------|---------|
| FastAPI | 0.104.1 | Async web framework |
| Python | 3.10+ | Core language |
| SQLAlchemy | 2.0.23 | Async ORM |
| SQLite/PostgreSQL | - | Database |
| JWT | - | Authentication |
| bcrypt | - | Password hashing |
| PyPDF2 | 3.0.1 | PDF text extraction |
| python-docx | 1.1.0 | DOCX text extraction |

### AI/LLM Integration
| Provider | Model | Purpose |
|----------|-------|---------|
| Ollama | GPT-OS 20B | Primary LLM (cloud/local) |
| Google Gemini | gemini-1.5-flash | First fallback |
| OpenAI | gpt-4o-mini | Second fallback |
| Custom Mock | - | Final fallback |

### Frontend
| Technology | Version | Purpose |
|------------|---------|---------|
| React | 18.2.0 | UI framework |
| Vite | 5.0 | Build tool |
| React Router | 6.20 | Navigation |
| TanStack Query | 5.12 | Data fetching |
| Zustand | 4.4 | State management |
| Axios | 1.6 | HTTP client |
| Three.js | 0.160 | 3D visualizations |
| React Three Fiber | 8.15 | React bindings for Three.js |
| Framer Motion | 10.16 | Animations |
| date-fns | 3.0 | Date formatting |

## 🔄 AI Fallback Chain

The system uses an intelligent fallback chain to ensure 100% uptime:
Ollama (GPT-OS 20B) → Gemini 1.5 Flash → GPT-4o-mini → Mock Analyzer

- **Primary**: Ollama (fast, cost-effective, can run locally)
- **First Fallback**: Google Gemini (high quality, good rate limits)
- **Second Fallback**: OpenAI GPT-4 (most capable, highest quality)
- **Final Fallback**: Mock analyzer (always works, never fails)

## 📊 Core Features

### Contract Processing
- Upload PDF, DOC, DOCX, TXT files (up to 50MB)
- Automatic text extraction and cleaning
- Contract type detection (NDA, SLA, MSA, etc.)
- Party and date extraction

### AI Analysis
- Executive summary generation
- Clause-by-clause risk assessment
- Smart recommendations for negotiation
- Risk scoring (0-100 with color coding)

### Obligation Management
- Automatic obligation extraction from contract text
- Due date detection
- Priority assignment (high/medium/low)
- Status tracking (pending/completed/overdue)

### Alert System
- Real-time alerts for high-risk clauses
- Upcoming obligation reminders
- Contract expiry notifications
- Unread badge indicators

💡 Use Cases
Legal Teams: Quickly review and analyze incoming contracts

Procurement: Assess vendor agreements and identify risks

Compliance: Track obligations and deadlines automatically

Sales: Review customer contracts before signing

Startups: Analyze NDAs, employment agreements, and SaaS terms
