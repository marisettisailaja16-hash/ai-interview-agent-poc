# AI Interview Agent – POC

A lightweight FastAPI POC that runs a dynamic interview flow:
- `/start` – begins a session (role, resumeText, tone)
- `/answer` – send an answer, get nextQuestion + coaching
- `/finish` – returns finalScore, strengths, improvements, transcript

## Tech
- FastAPI, Pydantic
- Uvicorn

## Run locally
```bash
pip install -r app/requirements.txt
uvicorn app.main:app --reload
