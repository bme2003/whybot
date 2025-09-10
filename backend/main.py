from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import Dict
from .models import PlanRequest, PlanResponse, TermBreakdown
from .planner import MultiCostPlanner

app = FastAPI(title="WHYBOT: Explainable Autonomy")

# Serve the frontend
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def root():
    return FileResponse("static/index.html")

@app.get("/health")
def health():
    return {"status":"ok"}

@app.post("/plan", response_model=PlanResponse)
def plan(req: PlanRequest):
    weights: Dict[str,float] = {
        "time": req.weights.time,
        "risk": req.weights.risk,
        "energy": req.weights.energy,
        "uncertainty": req.weights.uncertainty,
        "memory": req.weights.memory,
    }
    planner = MultiCostPlanner(
        width=req.width, height=req.height,
        obstacles=req.obstacles, hazards=req.hazards,
        weights=weights, seed=req.seed
    )
    path, ok, total, sums = planner.plan(req.start, req.goal)
    if not ok:
        return PlanResponse(
            path=[], found=False, total_cost=0.0, steps=0,
            breakdown=TermBreakdown(**sums),
            percentages={"time":0,"risk":0,"energy":0,"uncertainty":0,"memory":0},
            explanation="No path found. Try removing obstacles or moving start/goal."
        )
    steps = max(0, len(path)-1)
    # percentages
    total_terms = sum(sums.values()) or 1e-9
    pct = {k: (v/total_terms)*100.0 for k,v in sums.items()}
    # short explanation
    major = sorted(pct.items(), key=lambda kv: kv[1], reverse=True)[:2]
    major_str = " and ".join([f"{name} ({p:.1f}%)" for name,p in major])
    explanation = (
        f"Chose this route mainly due to {major_str}. "
        f"Total steps: {steps}. Time cost is per step, risk rises near walls, "
        f"energy penalizes turns, uncertainty comes from noisy areas, "
        f"and memory avoids prior bump spots."
    )
    return PlanResponse(
        path=path, found=True, total_cost=float(total), steps=steps,
        breakdown=TermBreakdown(**sums), percentages=pct, explanation=explanation
    )
