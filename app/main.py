# app/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
import uuid
from datetime import datetime

app = FastAPI(title="AI Interview Agent - POC")

# ===== In-memory session store (demo only) =====
class StartReq(BaseModel):
    resumeText: str
    role: str
    tone: Optional[str] = "supportive"

class StartResp(BaseModel):
    sessionId: str
    question: str

class AnswerReq(BaseModel):
    sessionId: str
    answer: str

class PartialScore(BaseModel):
    depth: int = 3

class AnswerResp(BaseModel):
    nextQuestion: Optional[str] = None
    coaching: Optional[str] = None
    partialScore: PartialScore = PartialScore()

class FinalScore(BaseModel):
    relevance: int = 4
    depth: int = 4
    clarity: int = 4
    star: int = 3
    technical: int = 4

class FinishResp(BaseModel):
    finalScore: FinalScore
    strengths: List[str]
    improvements: List[str]
    transcript: List[Dict[str, str]]

# in-memory store
SESSIONS: Dict[str, Dict] = {}

DEFAULT_QUESTIONS = [
    "Full Stack Java Developer: Tell me about a project you built recently. What was the impact?",
    "How did you design the architecture? Mention key components and choices.",
    "How did you design the architecture? Mention key components and choices.",
    "How did you design the architecture? Mention key components and choices.",
]

def _first_question(role: str) -> str:
    return DEFAULT_QUESTIONS[0].replace("Full Stack Java Developer", role)

def _coaching_for(answer: str) -> str:
    tips = []
    if "%" not in answer and "users" not in answer:
        tips.append("Add metrics (% / ms / users) and explain trade-offs.")
    if "Kafka" in answer or "microservice" in answer:
        tips.append("Explain why these choices were made and their impact.")
    return " ".join(tips) or "Good—add more depth with concrete outcomes."

@app.post("/start", response_model=StartResp)
def start(req: StartReq):
    sid = str(uuid.uuid4())
    q = _first_question(req.role)
    SESSIONS[sid] = {
        "createdAt": datetime.utcnow().isoformat(),
        "resumeText": req.resumeText,
        "role": req.role,
        "tone": req.tone,
        "qIndex": 0,
        "transcript": []
    }
    return StartResp(sessionId=sid, question=q)

@app.post("/answer", response_model=AnswerResp)
def answer(req: AnswerReq):
    s = SESSIONS.get(req.sessionId)
    if not s:
        raise HTTPException(status_code=404, detail="Invalid sessionId")

    qi = s["qIndex"]
    q = DEFAULT_QUESTIONS[qi] if qi < len(DEFAULT_QUESTIONS) else None
    s["transcript"].append({"q": q or "", "a": req.answer})

    s["qIndex"] += 1
    nextQ = DEFAULT_QUESTIONS[qi+1].replace(
        "Full Stack Java Developer", s["role"]
    ) if qi + 1 < len(DEFAULT_QUESTIONS) else None

    coaching = _co_
    # ---- very simple coaching heuristic ----
    ans = (req.answer or "").lower()
    tips = []

    # ask for metrics / users / latency if not mentioned
    if ("% " not in ans) and ("ms" not in ans) and ("latency" not in ans) and ("users" not in ans) and ("p95" not in ans):
        tips.append("Add metrics (% / ms / users) and explain trade-offs.")

    # explicitly ask for trade-offs if not mentioned
    if ("trade-off" not in ans) and ("tradeoffs" not in ans) and ("trade offs" not in ans):
        tips.append("Call out trade-offs.")

    coaching = " ".join(tips) or "Nice—keep going."

    return AnswerResp(
        nextQuestion=nextQ,
        coaching=coaching,
        partialScore=PartialScore(depth=s["qIndex"])
    )


# ================== FINISH ==================

class FinishResp(BaseModel):
    finalScore: Dict[str, int]
    strengths: List[str]
    improvements: List[str]
    transcript: List[Dict[str, str]]


@app.post("/finish", response_model=FinishResp)
def finish(sessionId: str):
    s = SESSIONS.pop(sessionId, None)
    if not s:
        raise HTTPException(status_code=404, detail="Invalid sessionId")

    transcript = s["transcript"]

    # very lightweight scoring for the POC
    final = {
        "relevance": 4,
        "depth": min(4, 1 + len(transcript)),   # more turns => a little more depth
        "clarity": 4,
        "star": 3,
        "technical": 4,
    }

    strengths = ["Clear architecture thinking"]
    improvements = ["Quote concrete metrics; explain trade-offs"]

    return FinishResp(
        finalScore=final,
        strengths=strengths,
        improvements=improvements,
        transcript=transcript,
    )
