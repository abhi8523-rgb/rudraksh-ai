<div align="center">

# 🔱 RUDRAKSH AI

### Sovereign Intelligence Suite

*A locally-hosted, privacy-first, modular AI platform*
*with hardcoded governance and autonomous execution capabilities*

[![Built with FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Frontend-Next.js-000000?style=for-the-badge&logo=next.js)](https://nextjs.org)
[![Ollama](https://img.shields.io/badge/LLM-Ollama-white?style=for-the-badge)](https://ollama.ai)
[![Docker](https://img.shields.io/badge/Deploy-Docker-2496ED?style=for-the-badge&logo=docker)](https://docker.com)

</div>

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    RUDRAKSH AI                          │
│                                                         │
│  ┌──────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ Next.js  │  │   FastAPI    │  │     Ollama       │  │
│  │ Frontend │──│   Backend    │──│   (Local LLM)    │  │
│  │ :3000    │  │   :8001      │  │   :11434         │  │
│  └──────────┘  └──────┬───────┘  └──────────────────┘  │
│                       │                                  │
│               ┌───────┴────────┐                        │
│               │   ChromaDB     │                        │
│               │ (Vector Store) │                        │
│               │   :8000        │                        │
│               └────────────────┘                        │
└─────────────────────────────────────────────────────────┘
```

## ⚡ Quick Start

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- 16GB+ RAM recommended
- 10GB+ free disk space (for models)

### Launch (One Command)

```bash
# Clone or navigate to the project directory
cd "Rudraksh AI"

# Copy environment template
cp .env.example .env

# Launch all services
docker compose up --build -d

# Pull a model (first time only)
docker exec -it rudraksh-ollama ollama pull llama3.2:3b
```

### Access
| Service | URL |
|---------|-----|
| 🖥️ Dashboard | [http://localhost:3000](http://localhost:3000) |
| ⚙️ API Docs | [http://localhost:8001/docs](http://localhost:8001/docs) |
| 🧠 Ollama | [http://localhost:11434](http://localhost:11434) |
| 📦 ChromaDB | [http://localhost:8000](http://localhost:8000) |

## 🔐 Governance

Rudraksh AI has a hardcoded Sovereign Administrator system. The system owner (`abhi8523@gmail.com`) has immutable, lifetime control including:

- Full system administration
- Audit log access
- Model management
- User management
- All metric dashboards

## 🧩 Modules

| Module | Description |
|--------|-------------|
| 💬 **Chat** | General-purpose AI chat with streaming responses |
| 👨‍💻 **Coders** | Code generation, refactoring, security scanning |
| 📱 **Social Media** | Content calendars, trend analysis, multi-platform drafts |
| 📊 **Marketing** | Campaign strategy, SEO analysis, customer personas |
| 🎓 **Students** | Study guides, concept explanation, citation tools |
| 🔬 **Research** | Deep RAG queries, hypothesis generation, literature reviews |
| ⚡ **Shivoham** | Autonomous task execution with DAG planning |

## 🛠️ Development

```bash
# Backend (standalone)
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend (standalone)
cd frontend
npm install
npm run dev
```

## 📄 License

Private & Proprietary — Sovereign ownership by `abhi8523@gmail.com`
