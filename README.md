# 🐙 A_I_Defend

An experimental **AI-driven defense system** built with Docker & Kubernetes concepts.  
The architecture is designed like an octopus:  
- **Brain**: Central model & logic (hidden, isolated).  
- **Arms**: Collectors & scanners you can interact with safely.  
- **Skin**: API & UI for operators.

---

## 🚀 Features (MVP)
- **Postgres (pgvector)** for events & detections.  
- **RabbitMQ** for message queue.  
- **Model server stub** (placeholder until real LLM).  
- **FastAPI backend** (events, detections, feedback, ask).  
- **Linux scanner container** that generates example events.  

---

## 📦 Getting Started

### 1. Clone repo
```bash
git clone https://github.com/USERNAME/defense-ai-octopus.git
cd defense-ai-octopus
