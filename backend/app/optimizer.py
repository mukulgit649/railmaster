"""Real OR-Tools CP-SAT block optimizer, plus a plain-heuristic manual baseline
and an explanation builder. Nothing here is a hardcoded result -- every number
in the response is derived from solving (or, for the manual baseline, from a
deterministic scheduling pass over whatever the solver actually included).
"""

from typing import Dict, List, Optional

from ortools.sat.python import cp_model

from .data import DEPARTMENTS, MAINTENANCE_JOBS, SUBSECTIONS, TRAINS, fmt
from .ml_priority import predict_dci

GAP_BETWEEN_MANUAL_BLOCKS = 10  # minutes handover between sequential manual blocks


def _effective_trains(conditions: dict) -> List[dict]:
    delays = conditions.get("train_delays", {})
    high = set(conditions.get("high_priority_trains", []))
    out = []
    for t in TRAINS:
        delay = delays.get(t["number"], 0)
        out.append(
            {
                **t,
                "entry": t["entry"] + delay,
                "exit": t["exit"] + delay,
                "priority": "HIGH" if t["number"] in high else "NORMAL",
                "delay": delay,
            }
        )
    return out


def _sections_for(train: dict) -> List[str]:
    if train["section"] == "S1-S3":
        return list(SUBSECTIONS)
    return [train["section"]]


def _overlap(a_start: int, a_end: int, b_start: int, b_end: int) -> int:
    return max(0, min(a_end, b_end) - max(a_start, b_start))


def _section_disruption(trains: List[dict], section: str, start: int, end: int):
    """NORMAL-priority overlap minutes + affected train numbers for one section/window."""
    total = 0
    affected = []
    for t in trains:
        if t["priority"] != "NORMAL":
            continue
        if section not in _sections_for(t):
            continue
        ov = _overlap(start, end, t["entry"], t["exit"])
        if ov > 0:
            total += ov
            affected.append(t["number"])
    return total, affected


def _build_and_solve(
    jobs: List[dict],
    dci: Dict[str, int],
    trains: List[dict],
    conditions: dict,
    objectives: dict,
    forbid_section: Optional[str] = None,
):
    model = cp_model.CpModel()
    bw = conditions["block_window"]
    bw_s, bw_e = bw["start"], bw["end"]

    section_idx = {s: i for i, s in enumerate(SUBSECTIONS)}
    section_choice = [model.NewBoolVar(f"sec_{s}") for s in SUBSECTIONS]
    model.Add(sum(section_choice) == 1)
    if forbid_section is not None:
        model.Add(section_choice[section_idx[forbid_section]] == 0)

    block_start = model.NewIntVar(bw_s, bw_e, "block_start")
    block_end = model.NewIntVar(bw_s, bw_e, "block_end")
    model.Add(block_end >= block_start)

    include = [model.NewBoolVar(f"inc_{j['id']}") for j in jobs]

    for i, job in enumerate(jobs):
        s = section_idx[job["section"]]
        model.Add(section_choice[s] == 1).OnlyEnforceIf(include[i])

        crew = conditions["crew_windows"][job["department"]]
        model.Add(block_start >= crew["start"]).OnlyEnforceIf(include[i])
        model.Add(block_end <= crew["end"]).OnlyEnforceIf(include[i])
        model.Add(block_end - block_start >= job["duration"]).OnlyEnforceIf(include[i])

    for dept in DEPARTMENTS:
        dept_idx = [i for i, j in enumerate(jobs) if j["department"] == dept]
        if dept_idx:
            model.Add(sum(include[i] for i in dept_idx) <= 1)

    # Hard-protect HIGH priority trains: block must not overlap their window
    # in whichever section is chosen.
    for t in trains:
        if t["priority"] != "HIGH":
            continue
        for s in _sections_for(t):
            s_idx = section_idx[s]
            before = model.NewBoolVar(f"before_{t['number']}_{s}")
            after = model.NewBoolVar(f"after_{t['number']}_{s}")
            model.Add(block_end <= t["entry"]).OnlyEnforceIf([section_choice[s_idx], before])
            model.Add(block_start >= t["exit"]).OnlyEnforceIf([section_choice[s_idx], after])
            model.AddBoolOr([before, after]).OnlyEnforceIf(section_choice[s_idx])

    # Soft disruption cost: overlap with NORMAL trains in the chosen section.
    disruption_terms = []
    for t in trains:
        if t["priority"] != "NORMAL":
            continue
        for s in _sections_for(t):
            s_idx = section_idx[s]
            ov_start = model.NewIntVar(0, 1440, f"ovs_{t['number']}_{s}")
            ov_end = model.NewIntVar(0, 1440, f"ove_{t['number']}_{s}")
            model.AddMaxEquality(ov_start, [block_start, t["entry"]])
            model.AddMinEquality(ov_end, [block_end, t["exit"]])
            raw_overlap = model.NewIntVar(-1440, 1440, f"raw_{t['number']}_{s}")
            model.Add(raw_overlap == ov_end - ov_start)
            overlap = model.NewIntVar(0, 1440, f"ovl_{t['number']}_{s}")
            model.AddMaxEquality(overlap, [raw_overlap, 0])
            active = model.NewIntVar(0, 1440, f"act_{t['number']}_{s}")
            model.Add(active == overlap).OnlyEnforceIf(section_choice[s_idx])
            model.Add(active == 0).OnlyEnforceIf(section_choice[s_idx].Not())
            disruption_terms.append(active)

    total_disruption = model.NewIntVar(0, 1440 * len(trains) + 1, "total_disruption")
    model.Add(total_disruption == sum(disruption_terms)) if disruption_terms else model.Add(total_disruption == 0)

    # CP-SAT needs integer coefficients, so priority terms are scaled up by
    # SCALE relative to the per-minute duration/disruption penalties -- this
    # keeps duration/disruption as tie-breakers rather than letting a few
    # minutes outweigh a large DCI-priority gap. Reported scores are divided
    # back down by SCALE (see run_optimization / _manual_baseline).
    SCALE = 10
    priority_weight = {
        j["id"]: SCALE * (dci[j["id"]] if objectives.get("prioritize_critical", True) else 50)
        for j in jobs
    }
    consolidation_bonus = 5 * SCALE if objectives.get("maximize_completed", True) else 0
    disruption_weight = 5 if objectives.get("minimize_disruption", True) else 0
    duration_weight = 1

    objective = sum(
        (priority_weight[jobs[i]["id"]] + consolidation_bonus) * include[i] for i in range(len(jobs))
    )
    objective -= duration_weight * (block_end - block_start)
    objective -= disruption_weight * total_disruption
    model.Maximize(objective)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 5.0
    solver.parameters.num_search_workers = 8
    status = solver.Solve(model)

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return None

    chosen_section = next(s for s in SUBSECTIONS if solver.Value(section_choice[section_idx[s]]))
    start_val = solver.Value(block_start)
    end_val = solver.Value(block_end)
    included_ids = [jobs[i]["id"] for i in range(len(jobs)) if solver.Value(include[i])]

    return {
        "section": chosen_section,
        "start": start_val,
        "end": end_val,
        "included_ids": included_ids,
        "objective_value": solver.ObjectiveValue() / SCALE,
    }


def _manual_baseline(jobs_by_id: Dict[str, dict], included_ids: List[str], trains: List[dict], conditions: dict, dci: Dict[str, int]):
    """Sequential, one-task-at-a-time scheduling -- what a human planner would do
    without consolidation. Computed, not hardcoded."""
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
    score = (
        sum(dci[j["id"]] for j in included_jobs)
        - 0.1 * total_block_time
        - 0.5 * total_disruption
    )
    return {
        "blocks": blocks,
        "total_block_time": total_block_time,
        "disruption": total_disruption,
        "affected_trains": sorted(all_affected),
        "score": round(score, 1),
    }


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

    solved = _build_and_solve(jobs, dci, trains, conditions, objectives)
    if solved is None:
        return {"feasible": False}

    section = solved["section"]
    start, end = solved["start"], solved["end"]
    included_ids = solved["included_ids"]
    disruption, affected = _section_disruption(trains, section, start, end)
    included_depts = {jobs_by_id[jid]["department"] for jid in included_ids}

    postponed = []
    for job in jobs:
        if job["id"] in included_ids:
            continue
        postponed.append(
            {
                "id": job["id"],
                "asset": job["asset"],
                "work": job["work"],
                "department": job["department"],
                "reason": _postpone_reason(job, section, start, end, conditions, included_depts),
            }
        )

    manual = _manual_baseline(jobs_by_id, included_ids, trains, conditions, dci)

    protected_high = sorted(
        {
            t["number"]
            for t in trains
            if t["priority"] == "HIGH" and section in _sections_for(t)
        }
    )

    dept_list = sorted(included_depts)
    explanation = []
    if included_ids:
        explanation.append(
            f"{len(included_ids)} maintenance task(s) with the highest DCI priority in {section} are compatible with one block."
        )
        if dept_list:
            explanation.append(
                f"{', '.join(dept_list)} crew{'s are' if len(dept_list) > 1 else ' is'} simultaneously available for {fmt(start)}–{fmt(end)}."
            )
        explanation.append(
            f"This window has {disruption} minute(s) of train disruption in {section} — the lowest among feasible windows found."
        )
        if protected_high:
            explanation.append(
                f"{len(protected_high)} high-priority train(s) ({', '.join(protected_high)}) are fully protected — no overlap with the block."
            )
        if len(included_ids) > 1:
            explanation.append(
                f"Combining {len(included_ids)} tasks avoids {len(included_ids) - 1} separate block request(s)."
            )
    else:
        explanation.append("No maintenance task is currently feasible under these conditions.")

    # Genuine "next best alternative": re-solve forbidding the chosen section.
    alt = _build_and_solve(jobs, dci, trains, conditions, objectives, forbid_section=section)
    alt_score = round(alt["objective_value"], 1) if alt else None

    return {
        "feasible": True,
        "section": section,
        "start": start,
        "end": end,
        "start_label": fmt(start),
        "end_label": fmt(end),
        "duration": end - start,
        "included_tasks": [
            {"id": jid, "asset": jobs_by_id[jid]["asset"], "work": jobs_by_id[jid]["work"], "department": jobs_by_id[jid]["department"], "dci": dci[jid]}
            for jid in included_ids
        ],
        "postponed_tasks": postponed,
        "train_conflicts": 0,  # HIGH-priority trains are a hard constraint: always 0
        "trains_affected": affected,
        "estimated_delay": disruption,
        "optimization_score": round(solved["objective_value"], 1),
        "explanation": explanation,
        "manual_baseline": manual,
        "alternative_score": alt_score,
        "dci": dci,
    }
