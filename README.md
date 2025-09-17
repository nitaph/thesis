# Creativity Study Backend (FastAPI) + Qualtrics Assets

Async FastAPI backend for:

- Big Five scoring (IPIP-50)
- Persona conditions (baseline, mirroring, complement, creative)
- Parallel LLM generation with caching
- Ratings intake and logging

Qualtrics assets:

- Embedded Data layout
- Fixed block order
- JavaScript for Big Five scoring, web service calls for generation and ratings (with mirrored ED)

---

## Quick Start

### 1) Requirements

- Python 3.11+
- PostgreSQL 14+ (asyncpg)
- (Optional) Redis 6+ for caching
- OpenAI API key

### 2) Install

```bash
cp .env.example .env
# edit .env
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```
