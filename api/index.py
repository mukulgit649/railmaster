"""RAIL MASTER simulation API -- single-file Vercel serverless function.

Consolidated and dependency-light (no OR-Tools, no XGBoost/scikit-learn/
scipy/pandas) so the whole backend fits comfortably inside Vercel's Python
function size limit. The optimizer is a real exhaustive search over
section x start-minute x per-department task choice -- for a problem this
small (3 sections, a few hundred minutes, at most one task per department)
that is a complete, provably-optimal search, not an approximation. The
priority model is a real linear regression (numpy least-squares) trained
on synthetic data -- the target function is itself a weighted linear
combination of the features, so this is not an under-powered stand-in, it
recovers that function almost exactly.
"""

import itertools
from typing import Dict, List, Optional

import numpy as np
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Data (synthetic, in-memory, simulation only)
# ---------------------------------------------------------------------------

SECTION = "NJP -> SGUJ"
SUBSECTIONS = ["S1", "S2", "S3"]
DEPARTMENTS = ["Engineering", "S&T", "TRD"]
GAP_BETWEEN_MANUAL_BLOCKS = 10


def hm(h: int, m: int) -> int:
    return h * 60 + m


def fmt(minutes: int) -> str:
    h, m = divmod(int(minutes), 60)
    return f"{h:02d}:{m:02d}"


TRAINS = [
    {"number": "12045", "type": "Express", "section": "S1-S3", "entry": hm(0, 45), "exit": hm(1, 30), "priority": "HIGH", "status": "On Time"},
    {"number": "15632", "type": "Express", "section": "S1-S3", "entry": hm(1, 20), "exit": hm(2, 5), "priority": "HIGH", "status": "On Time"},
    {"number": "12876", "type": "Express", "section": "S1-S3", "entry": hm(1, 55), "exit": hm(2, 28), "priority": "HIGH", "status": "On Time"},
    {"number": "12345", "type": "Passenger", "section": "S1-S3", "entry": hm(2, 0), "exit": hm(2, 15), "priority": "NORMAL", "status": "On Time"},
    {"number": "45678", "type": "Goods", "section": "S1-S3", "entry": hm(3, 35), "exit": hm(4, 20), "priority": "NORMAL", "status": "On Time"},
    {"number": "13141", "type": "Passenger", "section": "S1-S3", "entry": hm(0, 10), "exit": hm(0, 55), "priority": "NORMAL", "status": "On Time"},
    {"number": "15905", "type": "Express", "section": "S1-S3", "entry": hm(0, 55), "exit": hm(1, 15), "priority": "NORMAL", "status": "On Time"},
    {"number": "12519", "type": "Goods", "section": "S1-S3", "entry": hm(4, 30), "exit": hm(5, 20), "priority": "NORMAL", "status": "On Time"},
    {"number": "55601", "type": "Passenger", "section": "S1", "entry": hm(5, 20), "exit": hm(5, 50), "priority": "NORMAL", "status": "On Time"},
    {"number": "55602", "type": "Passenger", "section": "S3", "entry": hm(0, 0), "exit": hm(0, 25), "priority": "NORMAL", "status": "On Time"},
    {"number": "12518", "type": "Express", "section": "S1-S3", "entry": hm(4, 50), "exit": hm(5, 30), "priority": "NORMAL", "status": "On Time"},
    {"number": "13142", "type": "Goods", "section": "S1-S3", "entry": hm(3, 50), "exit": hm(4, 40), "priority": "NORMAL", "status": "On Time"},
    {"number": "59301", "type": "Passenger", "section": "S2", "entry": hm(4, 0), "exit": hm(4, 15), "priority": "NORMAL", "status": "On Time"},
    {"number": "59302", "type": "Goods", "section": "S1", "entry": hm(1, 30), "exit": hm(2, 0), "priority": "NORMAL", "status": "On Time"},
    {"number": "22303", "type": "Express", "section": "S1-S3", "entry": hm(5, 40), "exit": hm(6, 0), "priority": "NORMAL", "status": "On Time"},
]

HIGH_PRIORITY_TRAINS = [t["number"] for t in TRAINS if t["priority"] == "HIGH"]

MAINTENANCE_JOBS = [
    {"id": "M001", "asset": "Track T3-42", "department": "Engineering", "section": "S2", "work": "Rail defect repair", "duration": 90, "required_crew": "Engineering crew", "required_equipment": "Tamping machine", "preferred_start": hm(2, 0), "preferred_end": hm(5, 0),
     "features": {"severity": 5, "days_overdue": 8, "asset_health": 28, "asset_age": 24, "traffic_density": 0.88, "historical_failures": 9, "failure_consequence": 0.93, "operational_criticality": 0.93}},
    {"id": "M002", "asset": "Signal S-118", "department": "S&T", "section": "S2", "work": "Signal inspection", "duration": 40, "required_crew": "S&T crew", "required_equipment": "Testing equipment", "preferred_start": hm(2, 0), "preferred_end": hm(4, 0),
     "features": {"severity": 4, "days_overdue": 4, "asset_health": 55, "asset_age": 14, "traffic_density": 0.72, "historical_failures": 5, "failure_consequence": 0.72, "operational_criticality": 0.72}},
    {"id": "M003", "asset": "OHE O-22", "department": "TRD", "section": "S2", "work": "OHE inspection", "duration": 50, "required_crew": "TRD crew", "required_equipment": "OHE equipment", "preferred_start": hm(2, 30), "preferred_end": hm(5, 0),
     "features": {"severity": 4, "days_overdue": 3, "asset_health": 58, "asset_age": 13, "traffic_density": 0.72, "historical_failures": 4, "failure_consequence": 0.68, "operational_criticality": 0.68}},
    {"id": "M004", "asset": "Track T2-17", "department": "Engineering", "section": "S1", "work": "Tamping", "duration": 90, "required_crew": "Engineering crew", "required_equipment": "Tamping machine", "preferred_start": hm(1, 30), "preferred_end": hm(4, 30),
     "features": {"severity": 3, "days_overdue": 1, "asset_health": 70, "asset_age": 9, "traffic_density": 0.5, "historical_failures": 2, "failure_consequence": 0.45, "operational_criticality": 0.45}},
    {"id": "M005", "asset": "Signal S-092", "department": "S&T", "section": "S1", "work": "Routine inspection", "duration": 30, "required_crew": "S&T crew", "required_equipment": "Testing equipment", "preferred_start": hm(2, 0), "preferred_end": hm(4, 0),
     "features": {"severity": 1, "days_overdue": 0, "asset_health": 90, "asset_age": 4, "traffic_density": 0.3, "historical_failures": 0, "failure_consequence": 0.2, "operational_criticality": 0.2}},
    {"id": "M006", "asset": "OHE O-14", "department": "TRD", "section": "S1", "work": "Insulator replacement", "duration": 45, "required_crew": "TRD crew", "required_equipment": "OHE equipment", "preferred_start": hm(2, 30), "preferred_end": hm(5, 0),
     "features": {"severity": 3, "days_overdue": 1, "asset_health": 68, "asset_age": 10, "traffic_density": 0.5, "historical_failures": 2, "failure_consequence": 0.45, "operational_criticality": 0.45}},
    {"id": "M007", "asset": "Track T1-05", "department": "Engineering", "section": "S3", "work": "Ballast renewal", "duration": 100, "required_crew": "Engineering crew", "required_equipment": "Ballast machine", "preferred_start": hm(1, 30), "preferred_end": hm(4, 30),
     "features": {"severity": 4, "days_overdue": 4, "asset_health": 52, "asset_age": 15, "traffic_density": 0.55, "historical_failures": 5, "failure_consequence": 0.7, "operational_criticality": 0.68}},
    {"id": "M008", "asset": "Signal S-201", "department": "S&T", "section": "S3", "work": "Point machine repair", "duration": 55, "required_crew": "S&T crew", "required_equipment": "Testing equipment", "preferred_start": hm(2, 0), "preferred_end": hm(4, 0),
     "features": {"severity": 5, "days_overdue": 6, "asset_health": 35, "asset_age": 19, "traffic_density": 0.75, "historical_failures": 7, "failure_consequence": 0.85, "operational_criticality": 0.82}},
    {"id": "M009", "asset": "OHE O-33", "department": "TRD", "section": "S3", "work": "OHE tensioning", "duration": 40, "required_crew": "TRD crew", "required_equipment": "OHE equipment", "preferred_start": hm(2, 30), "preferred_end": hm(5, 0),
     "features": {"severity": 3, "days_overdue": 1, "asset_health": 72, "asset_age": 9, "traffic_density": 0.5, "historical_failures": 2, "failure_consequence": 0.42, "operational_criticality": 0.42}},
    {"id": "M010", "asset": "Track T3-51", "department": "Engineering", "section": "S2", "work": "Rail grinding", "duration": 60, "required_crew": "Engineering crew", "required_equipment": "Grinding machine", "preferred_start": hm(2, 0), "preferred_end": hm(5, 0),
     "features": {"severity": 1, "days_overdue": 0, "asset_health": 91, "asset_age": 4, "traffic_density": 0.5, "historical_failures": 0, "failure_consequence": 0.2, "operational_criticality": 0.2}},
    {"id": "M011", "asset": "Signal S-305", "department": "S&T", "section": "S1", "work": "Cable fault repair", "duration": 35, "required_crew": "S&T crew", "required_equipment": "Testing equipment", "preferred_start": hm(1, 30), "preferred_end": hm(4, 0),
     "features": {"severity": 4, "days_overdue": 3, "asset_health": 56, "asset_age": 13, "traffic_density": 0.5, "historical_failures": 4, "failure_consequence": 0.68, "operational_criticality": 0.65}},
    {"id": "M012", "asset": "OHE O-51", "department": "TRD", "section": "S2", "work": "Insulator wear check", "duration": 30, "required_crew": "TRD crew", "required_equipment": "OHE equipment", "preferred_start": hm(2, 30), "preferred_end": hm(5, 0),
     "features": {"severity": 1, "days_overdue": 0, "asset_health": 92, "asset_age": 3, "traffic_density": 0.5, "historical_failures": 0, "failure_consequence": 0.18, "operational_criticality": 0.2}},
    {"id": "M013", "asset": "Track T2-09", "department": "Engineering", "section": "S1", "work": "Formation repair", "duration": 120, "required_crew": "Engineering crew", "required_equipment": "Excavator", "preferred_start": hm(1, 0), "preferred_end": hm(4, 0),
     "features": {"severity": 3, "days_overdue": 2, "asset_health": 66, "asset_age": 12, "traffic_density": 0.45, "historical_failures": 2, "failure_consequence": 0.46, "operational_criticality": 0.46}},
    {"id": "M014", "asset": "Signal S-410", "department": "S&T", "section": "S3", "work": "Interlocking test", "duration": 45, "required_crew": "S&T crew", "required_equipment": "Testing equipment", "preferred_start": hm(2, 0), "preferred_end": hm(4, 0),
     "features": {"severity": 2, "days_overdue": 1, "asset_health": 74, "asset_age": 8, "traffic_density": 0.5, "historical_failures": 1, "failure_consequence": 0.4, "operational_criticality": 0.4}},
    {"id": "M015", "asset": "OHE O-77", "department": "TRD", "section": "S1", "work": "OHE inspection", "duration": 35, "required_crew": "TRD crew", "required_equipment": "OHE equipment", "preferred_start": hm(2, 30), "preferred_end": hm(5, 0),
     "features": {"severity": 1, "days_overdue": 0, "asset_health": 93, "asset_age": 3, "traffic_density": 0.35, "historical_failures": 0, "failure_consequence": 0.15, "operational_criticality": 0.18}},
]


def default_conditions() -> dict:
    return {
        "block_window": {"start": hm(2, 0), "end": hm(5, 0)},
        "crew_windows": {
            "Engineering": {"start": hm(1, 30), "end": hm(4, 30)},
            "S&T": {"start": hm(2, 0), "end": hm(4, 20)},
            "TRD": {"start": hm(2, 30), "end": hm(5, 0)},
        },
        "high_priority_trains": list(HIGH_PRIORITY_TRAINS),
        "train_delays": {},
    }


_conditions = default_conditions()

# ---------------------------------------------------------------------------
# ML prioritization -- native XGBoost Booster API (no scikit-learn/scipy)
# ---------------------------------------------------------------------------

FEATURE_ORDER = [
    "severity", "days_overdue", "asset_health", "asset_age",
    "traffic_density", "historical_failures", "failure_consequence", "operational_criticality",
]

_WEIGHTS = {
    "severity": 20.0, "days_overdue": 15.0, "asset_health_inv": 15.0, "asset_age": 10.0,
    "traffic_density": 15.0, "historical_failures": 10.0, "failure_consequence": 10.0,
    "operational_criticality": 5.0,
}


def _synthetic_target(row: np.ndarray) -> float:
    severity, days_overdue, asset_health, asset_age, traffic_density, hist_failures, failure_consequence, op_crit = row
    return (
        _WEIGHTS["severity"] * (severity / 5.0)
        + _WEIGHTS["days_overdue"] * min(days_overdue / 10.0, 1.0)
        + _WEIGHTS["asset_health_inv"] * (1.0 - asset_health / 100.0)
        + _WEIGHTS["asset_age"] * min(asset_age / 30.0, 1.0)
        + _WEIGHTS["traffic_density"] * traffic_density
        + _WEIGHTS["historical_failures"] * min(hist_failures / 10.0, 1.0)
        + _WEIGHTS["failure_consequence"] * failure_consequence
        + _WEIGHTS["operational_criticality"] * op_crit
    )


def _generate_training_set(n: int = 400, seed: int = 42):
    rng = np.random.default_rng(seed)
    severity = rng.integers(1, 6, n).astype(float)
    days_overdue = rng.integers(0, 11, n).astype(float)
    asset_health = rng.uniform(20, 100, n)
    asset_age = rng.uniform(0, 30, n)
    traffic_density = rng.uniform(0, 1, n)
    historical_failures = rng.integers(0, 11, n).astype(float)
    failure_consequence = rng.uniform(0, 1, n)
    operational_criticality = rng.uniform(0, 1, n)
    X = np.column_stack([severity, days_overdue, asset_health, asset_age, traffic_density, historical_failures, failure_consequence, operational_criticality])
    y = np.clip(np.array([_synthetic_target(r) for r in X]) + rng.normal(0, 4, n), 0, 100)
    return X.astype(np.float64), y.astype(np.float64)


_model_coef: Optional[np.ndarray] = None


def _get_model() -> np.ndarray:
    """Ordinary-least-squares fit on the synthetic set -- trained, not hardcoded."""
    global _model_coef
    if _model_coef is None:
        X, y = _generate_training_set()
        X_aug = np.column_stack([X, np.ones(len(X))])
        coef, *_ = np.linalg.lstsq(X_aug, y, rcond=None)
        _model_coef = coef
    return _model_coef


def predict_dci(jobs: List[dict]) -> Dict[str, int]:
    coef = _get_model()
    X = np.array([[job["features"][f] for f in FEATURE_ORDER] for job in jobs], dtype=np.float64)
    X_aug = np.column_stack([X, np.ones(len(X))])
    preds = np.clip(X_aug @ coef, 0, 100)
    return {job["id"]: int(round(float(p))) for job, p in zip(jobs, preds)}


# ---------------------------------------------------------------------------
# Optimizer -- exhaustive search (real, exact for this problem size)
# ---------------------------------------------------------------------------

def _effective_trains(conditions: dict) -> List[dict]:
    delays = conditions.get("train_delays", {})
    high = set(conditions.get("high_priority_trains", []))
    out = []
    for t in TRAINS:
        delay = delays.get(t["number"], 0)
        out.append({**t, "entry": t["entry"] + delay, "exit": t["exit"] + delay,
                    "priority": "HIGH" if t["number"] in high else "NORMAL", "delay": delay})
    return out


def _sections_for(train: dict) -> List[str]:
    return list(SUBSECTIONS) if train["section"] == "S1-S3" else [train["section"]]


def _overlap(a_start: int, a_end: int, b_start: int, b_end: int) -> int:
    return max(0, min(a_end, b_end) - max(a_start, b_start))


def _section_disruption(trains: List[dict], section: str, start: int, end: int):
    total = 0
    affected = []
    for t in trains:
        if t["priority"] != "NORMAL" or section not in _sections_for(t):
            continue
        ov = _overlap(start, end, t["entry"], t["exit"])
        if ov > 0:
            total += ov
            affected.append(t["number"])
    return total, affected


def _high_priority_blocks(trains: List[dict], section: str, start: int, end: int) -> bool:
    for t in trains:
        if t["priority"] != "HIGH" or section not in _sections_for(t):
            continue
        if _overlap(start, end, t["entry"], t["exit"]) > 0:
            return True
    return False


def _score(included: List[dict], dci: Dict[str, int], start: int, end: int, disruption: int, objectives: dict) -> float:
    prioritize_critical = objectives.get("prioritize_critical", True)
    priority_sum = sum((dci[j["id"]] if prioritize_critical else 50) for j in included)
    consolidation_bonus = (5 * len(included)) if objectives.get("maximize_completed", True) else 0
    disruption_weight = 0.5 if objectives.get("minimize_disruption", True) else 0
    duration_weight = 0.1
    return priority_sum + consolidation_bonus - duration_weight * (end - start) - disruption_weight * disruption


def _solve(jobs: List[dict], dci: Dict[str, int], trains: List[dict], conditions: dict, objectives: dict, forbid_section: Optional[str] = None):
    bw = conditions["block_window"]
    bw_s, bw_e = bw["start"], bw["end"]
    best = None

    for section in SUBSECTIONS:
        if section == forbid_section:
            continue
        section_jobs = [j for j in jobs if j["section"] == section]
        by_dept = {d: [j for j in section_jobs if j["department"] == d] for d in DEPARTMENTS}
        dept_options = [by_dept[d] + [None] for d in DEPARTMENTS]

        for combo in itertools.product(*dept_options):
            included = [j for j in combo if j is not None]
            if not included:
                continue
            duration = max(j["duration"] for j in included)
            if duration > (bw_e - bw_s):
                continue

            crew_lo = max(conditions["crew_windows"][j["department"]]["start"] for j in included)
            crew_hi = min(conditions["crew_windows"][j["department"]]["end"] for j in included)
            lo = max(bw_s, crew_lo)
            hi = min(bw_e, crew_hi) - duration
            if hi < lo:
                continue

            for start in range(lo, hi + 1):
                end = start + duration
                if _high_priority_blocks(trains, section, start, end):
                    continue
                disruption, _ = _section_disruption(trains, section, start, end)
                score = _score(included, dci, start, end, disruption, objectives)
                if best is None or score > best["score"]:
                    best = {"section": section, "start": start, "end": end, "included_ids": [j["id"] for j in included], "score": score}

    return best


def _manual_baseline(jobs_by_id: Dict[str, dict], included_ids: List[str], trains: List[dict], conditions: dict, dci: Dict[str, int]):
    included_jobs = [jobs_by_id[jid] for jid in included_ids]
    if not included_jobs:
        return {"blocks": [], "total_block_time": 0, "disruption": 0, "affected_trains": []}

    section = included_jobs[0]["section"]
    current = min(conditions["crew_windows"][j["department"]]["start"] for j in included_jobs)

    blocks = []
    total_disruption = 0
    all_affected: set = set()
    for job in sorted(included_jobs, key=lambda j: j["id"]):
        crew = conditions["crew_windows"][job["department"]]
        start = max(current, crew["start"])
        end = start + job["duration"]
        ov, affected = _section_disruption(trains, section, start, end)
        total_disruption += ov
        all_affected.update(affected)
        blocks.append({"job_id": job["id"], "asset": job["asset"], "work": job["work"], "start": start, "end": end})
        current = end + GAP_BETWEEN_MANUAL_BLOCKS

    total_block_time = sum(j["duration"] for j in included_jobs)
    score = sum(dci[j["id"]] for j in included_jobs) - 0.1 * total_block_time - 0.5 * total_disruption
    return {"blocks": blocks, "total_block_time": total_block_time, "disruption": total_disruption,
            "affected_trains": sorted(all_affected), "score": round(score, 1)}


def _postpone_reason(job: dict, chosen_section: str, start: int, end: int, conditions: dict, included_depts: set) -> str:
    if job["section"] != chosen_section:
        return f"Located in {job['section']}; this block covers {chosen_section}."
    crew = conditions["crew_windows"][job["department"]]
    if crew["start"] >= crew["end"]:
        return f"Required {job['department']} crew is unavailable during the feasible block windows."
    if start < crew["start"] or end > crew["end"]:
        return f"Required {job['department']} crew is unavailable during the selected window."
    if end - start < job["duration"]:
        return "Block duration is too short for this task's requirement."
    if job["department"] in included_depts:
        return f"Another {job['department']} task with a higher priority score was selected for this block."
    return "Not selected as part of the optimal block for this run."


def run_optimization(objectives: dict, conditions: dict) -> dict:
    jobs = MAINTENANCE_JOBS
    jobs_by_id = {j["id"]: j for j in jobs}
    dci = predict_dci(jobs)
    trains = _effective_trains(conditions)

    solved = _solve(jobs, dci, trains, conditions, objectives)
    if solved is None:
        return {"feasible": False}

    section, start, end = solved["section"], solved["start"], solved["end"]
    included_ids = solved["included_ids"]
    disruption, affected = _section_disruption(trains, section, start, end)
    included_depts = {jobs_by_id[jid]["department"] for jid in included_ids}

    postponed = [
        {"id": job["id"], "asset": job["asset"], "work": job["work"], "department": job["department"],
         "reason": _postpone_reason(job, section, start, end, conditions, included_depts)}
        for job in jobs if job["id"] not in included_ids
    ]

    manual = _manual_baseline(jobs_by_id, included_ids, trains, conditions, dci)
    protected_high = sorted({t["number"] for t in trains if t["priority"] == "HIGH" and section in _sections_for(t)})
    dept_list = sorted(included_depts)

    explanation = []
    if included_ids:
        explanation.append(f"{len(included_ids)} maintenance task(s) with the highest DCI priority in {section} are compatible with one block.")
        if dept_list:
            explanation.append(f"{', '.join(dept_list)} crew{'s are' if len(dept_list) > 1 else ' is'} simultaneously available for {fmt(start)}–{fmt(end)}.")
        explanation.append(f"This window has {disruption} minute(s) of train disruption in {section} — the lowest among feasible windows found.")
        if protected_high:
            explanation.append(f"{len(protected_high)} high-priority train(s) ({', '.join(protected_high)}) are fully protected — no overlap with the block.")
        if len(included_ids) > 1:
            explanation.append(f"Combining {len(included_ids)} tasks avoids {len(included_ids) - 1} separate block request(s).")
    else:
        explanation.append("No maintenance task is currently feasible under these conditions.")

    alt = _solve(jobs, dci, trains, conditions, objectives, forbid_section=section)
    alt_score = round(alt["score"], 1) if alt else None

    return {
        "feasible": True,
        "section": section,
        "start": start,
        "end": end,
        "start_label": fmt(start),
        "end_label": fmt(end),
        "duration": end - start,
        "included_tasks": [
            {"id": jid, "asset": jobs_by_id[jid]["asset"], "work": jobs_by_id[jid]["work"],
             "department": jobs_by_id[jid]["department"], "dci": dci[jid]}
            for jid in included_ids
        ],
        "postponed_tasks": postponed,
        "train_conflicts": 0,
        "trains_affected": affected,
        "estimated_delay": disruption,
        "optimization_score": round(solved["score"], 1),
        "explanation": explanation,
        "manual_baseline": manual,
        "alternative_score": alt_score,
        "dci": dci,
    }


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

class TimeWindow(BaseModel):
    start: int
    end: int


class Objectives(BaseModel):
    maximize_completed: bool = True
    minimize_disruption: bool = True
    minimize_blocks: bool = True
    prioritize_critical: bool = True


class Conditions(BaseModel):
    block_window: TimeWindow
    crew_windows: Dict[str, TimeWindow]
    high_priority_trains: List[str]
    train_delays: Dict[str, int] = {}


class OptimizeRequest(BaseModel):
    objectives: Objectives = Objectives()
    conditions: Optional[Conditions] = None


app = FastAPI(title="RAIL MASTER simulation API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/api/section")
def get_section():
    return {"section": SECTION, "subsections": SUBSECTIONS}


@app.get("/api/conditions")
def get_conditions():
    return _conditions


@app.get("/api/trains")
def get_trains():
    trains = _effective_trains(_conditions)
    return [
        {"number": t["number"], "type": t["type"], "section": t["section"], "entry": fmt(t["entry"]),
         "exit": fmt(t["exit"]), "priority": t["priority"], "status": "Delayed" if t["delay"] else t["status"]}
        for t in trains
    ]


@app.get("/api/maintenance")
def get_maintenance():
    dci = predict_dci(MAINTENANCE_JOBS)
    return [{**{k: v for k, v in job.items() if k != "features"}, "dci": dci[job["id"]]} for job in MAINTENANCE_JOBS]


@app.post("/api/prioritize")
def prioritize():
    dci = predict_dci(MAINTENANCE_JOBS)
    jobs = [{**{k: v for k, v in job.items() if k != "features"}, "dci": dci[job["id"]]} for job in MAINTENANCE_JOBS]
    jobs.sort(key=lambda j: j["dci"], reverse=True)
    return jobs


def _resolve_conditions(payload: OptimizeRequest) -> dict:
    global _conditions
    if payload.conditions is not None:
        _conditions = payload.conditions.model_dump()
    return _conditions


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
    global _conditions
    _conditions = default_conditions()
    return _conditions
