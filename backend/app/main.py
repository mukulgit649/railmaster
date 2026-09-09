from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import state
from .data import MAINTENANCE_JOBS, SECTION, SUBSECTIONS, fmt
from .ml_priority import predict_dci
from .optimizer import _effective_trains, run_optimization
from .schemas import OptimizeRequest

app = FastAPI(title="RAIL MASTER simulation API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def warm_model():
    predict_dci(MAINTENANCE_JOBS)  # trains the XGBoost model once, up front


@app.get("/api/section")
def get_section():
    return {"section": SECTION, "subsections": SUBSECTIONS}


@app.get("/api/conditions")
def get_conditions():
    return state.get_conditions()


@app.get("/api/trains")
def get_trains():
    conditions = state.get_conditions()
    trains = _effective_trains(conditions)
    return [
        {
            "number": t["number"],
            "type": t["type"],
            "section": t["section"],
            "entry": fmt(t["entry"]),
            "exit": fmt(t["exit"]),
            "priority": t["priority"],
            "status": "Delayed" if t["delay"] else t["status"],
        }
        for t in trains
    ]


@app.get("/api/maintenance")
def get_maintenance():
    dci = predict_dci(MAINTENANCE_JOBS)
    return [
        {**{k: v for k, v in job.items() if k != "features"}, "dci": dci[job["id"]]}
        for job in MAINTENANCE_JOBS
    ]


@app.post("/api/prioritize")
def prioritize():
    dci = predict_dci(MAINTENANCE_JOBS)
    jobs = [
        {**{k: v for k, v in job.items() if k != "features"}, "dci": dci[job["id"]]}
        for job in MAINTENANCE_JOBS
    ]
    jobs.sort(key=lambda j: j["dci"], reverse=True)
    return jobs


def _resolve_conditions(payload: OptimizeRequest) -> dict:
    if payload.conditions is not None:
        conditions = payload.conditions.model_dump()
        state.set_conditions(conditions)
        return conditions
    return state.get_conditions()


@app.post("/api/optimize")
def optimize(payload: OptimizeRequest):
    conditions = _resolve_conditions(payload)
    return run_optimization(payload.objectives.model_dump(), conditions)


@app.post("/api/reoptimize")
def reoptimize(payload: OptimizeRequest):
    conditions = _resolve_conditions(payload)
    return run_optimization(payload.objectives.model_dump(), conditions)


@app.post("/api/reset")
def reset():
    return state.reset_conditions()
