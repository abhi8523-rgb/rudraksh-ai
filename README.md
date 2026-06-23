# 🔱 Neel AI — Sovereign Intelligence Suite

> A privacy-first, locally-hosted AI platform with autonomous execution, modular industry verticals, and hardcoded governance.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![Next.js 15](https://img.shields.io/badge/Next.js-15-black.svg)](https://nextjs.org)

## 🌟 What is Neel AI?

Neel AI is a **complete AI platform** that runs entirely on your local machine. No cloud, no API fees, no data leaving your device. It combines:

- 🧠 **Multiple Local LLMs** via Ollama (Llama, DeepSeek, Mistral, CodeLlama)
- 📚 **RAG Pipeline** via ChromaDB (upload documents, ask questions)
- 🔱 **Trident Engine** — autonomous task execution with DAG planning
- 🔐 **Sovereign Governance** — hardcoded admin control (abhi8523@gmail.com)
- 🎨 **8 Specialized Modules** — each with purpose-built AI tools

## 🚀 Quick Start

### Prerequisites
- [Ollama](https://ollama.com) — Local LLM server
- [Python 3.11+](https://python.org) — Backend
- [Node.js 20+](https://nodejs.org) — Frontend

### One-Click Launch (Windows)
```
Double-click: start.bat
```

### Manual Setup
```bash
# Terminal 1: Ollama
ollama serve
ollama pull llama3.2:3b
ollama pull nomic-embed-text

# Terminal 2: Backend
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8001 --reload

# Terminal 3: Frontend
cd frontend
npm install
npm run dev
```

## 📱 Modules

| Module | Icon | Description |
|--------|------|-------------|
| **Chat** | 💬 | Intelligent conversations with any loaded model |
| **Coders** | ⚡ | Code generation, refactoring, documentation, security |
| **Social Media** | 📱 | Content planning, trend analysis, multi-platform drafts |
| **Marketing** | 📊 | Campaign strategy, SEO, A/B testing, personas |
| **Students** | 🎓 | Study guides, concept explanations, citations |
| **Research** | 🔬 | RAG-powered deep research & literature review |
| **Trident** | 🔱 | Autonomous execution engine with DAG visualization |
| **Sovereign** | 👑 | Admin dashboard, metrics, audit logs |

## 🏗️ Architecture

```
Neel AI
├── backend/          # FastAPI (Python)
│   ├── config/       # Governance & settings
│   ├── auth/         # JWT + RBAC
│   ├── llm/          # Ollama & LM Studio clients
│   ├── memory/       # ChromaDB RAG pipeline
│   ├── modules/      # 5 functional modules
│   ├── trident/      # Autonomous execution engine
│   └── sovereign/    # Audit & metrics
├── frontend/         # Next.js (TypeScript)
│   ├── src/app/      # 8 module pages
│   ├── src/components/ # UI components
│   └── src/hooks/    # React hooks
└── docker-compose.yml
```

## 🔒 Governance

The Sovereign Administrator (`abhi8523@gmail.com`) is **permanently hardcoded** into the source code. This identity cannot be overridden, impersonated, or revoked at runtime.

## 🛠️ Tech Stack

- **Backend**: Python 3.11+ / FastAPI / Pydantic
- **Frontend**: Next.js 15 / TypeScript / Tailwind CSS / Framer Motion
- **LLM**: Ollama (local) / LM Studio (local)
- **Vector DB**: ChromaDB
- **Auth**: JWT + bcrypt + RBAC
- **Containerization**: Docker Compose

## 📄 License

MIT License — Built with 🔱 by Neel AI
