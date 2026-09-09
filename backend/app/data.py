"""Synthetic demo data for the NJP -> SGUJ section. Simulation only, in-memory."""

SECTION = "NJP -> SGUJ"
SUBSECTIONS = ["S1", "S2", "S3"]

DEPARTMENTS = ["Engineering", "S&T", "TRD"]


def hm(h: int, m: int) -> int:
    """Hours/minutes -> minutes-from-midnight."""
    return h * 60 + m


def fmt(minutes: int) -> str:
    h, m = divmod(int(minutes), 60)
    return f"{h:02d}:{m:02d}"


# ---------------------------------------------------------------------------
# Trains
# ---------------------------------------------------------------------------
# section: "S1-S3" for through trains (occupy every subsection while in the
# corridor), or a single subsection for local/shunting movements.

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


# ---------------------------------------------------------------------------
# Maintenance jobs
# ---------------------------------------------------------------------------
# ML feature vectors live alongside each job; DCI itself is computed by the
# XGBoost model at request time, never hardcoded.

MAINTENANCE_JOBS = [
    {
        "id": "M001", "asset": "Track T3-42", "department": "Engineering", "section": "S2",
        "work": "Rail defect repair", "duration": 90, "required_crew": "Engineering crew",
        "required_equipment": "Tamping machine", "preferred_start": hm(2, 0), "preferred_end": hm(5, 0),
        "features": {"severity": 5, "days_overdue": 8, "asset_health": 28, "asset_age": 24,
                     "traffic_density": 0.88, "historical_failures": 9, "failure_consequence": 0.93,
                     "operational_criticality": 0.93},
    },
    {
        "id": "M002", "asset": "Signal S-118", "department": "S&T", "section": "S2",
        "work": "Signal inspection", "duration": 40, "required_crew": "S&T crew",
        "required_equipment": "Testing equipment", "preferred_start": hm(2, 0), "preferred_end": hm(4, 0),
        "features": {"severity": 4, "days_overdue": 4, "asset_health": 55, "asset_age": 14,
                     "traffic_density": 0.72, "historical_failures": 5, "failure_consequence": 0.72,
                     "operational_criticality": 0.72},
    },
    {
        "id": "M003", "asset": "OHE O-22", "department": "TRD", "section": "S2",
        "work": "OHE inspection", "duration": 50, "required_crew": "TRD crew",
        "required_equipment": "OHE equipment", "preferred_start": hm(2, 30), "preferred_end": hm(5, 0),
        "features": {"severity": 4, "days_overdue": 3, "asset_health": 58, "asset_age": 13,
                     "traffic_density": 0.72, "historical_failures": 4, "failure_consequence": 0.68,
                     "operational_criticality": 0.68},
    },
    {
        "id": "M004", "asset": "Track T2-17", "department": "Engineering", "section": "S1",
        "work": "Tamping", "duration": 90, "required_crew": "Engineering crew",
        "required_equipment": "Tamping machine", "preferred_start": hm(1, 30), "preferred_end": hm(4, 30),
        "features": {"severity": 3, "days_overdue": 1, "asset_health": 70, "asset_age": 9,
                     "traffic_density": 0.5, "historical_failures": 2, "failure_consequence": 0.45,
                     "operational_criticality": 0.45},
    },
    {
        "id": "M005", "asset": "Signal S-092", "department": "S&T", "section": "S1",
        "work": "Routine inspection", "duration": 30, "required_crew": "S&T crew",
        "required_equipment": "Testing equipment", "preferred_start": hm(2, 0), "preferred_end": hm(4, 0),
        "features": {"severity": 1, "days_overdue": 0, "asset_health": 90, "asset_age": 4,
                     "traffic_density": 0.3, "historical_failures": 0, "failure_consequence": 0.2,
                     "operational_criticality": 0.2},
    },
    {
        "id": "M006", "asset": "OHE O-14", "department": "TRD", "section": "S1",
        "work": "Insulator replacement", "duration": 45, "required_crew": "TRD crew",
        "required_equipment": "OHE equipment", "preferred_start": hm(2, 30), "preferred_end": hm(5, 0),
        "features": {"severity": 3, "days_overdue": 1, "asset_health": 68, "asset_age": 10,
                     "traffic_density": 0.5, "historical_failures": 2, "failure_consequence": 0.45,
                     "operational_criticality": 0.45},
    },
    {
        "id": "M007", "asset": "Track T1-05", "department": "Engineering", "section": "S3",
        "work": "Ballast renewal", "duration": 100, "required_crew": "Engineering crew",
        "required_equipment": "Ballast machine", "preferred_start": hm(1, 30), "preferred_end": hm(4, 30),
        "features": {"severity": 4, "days_overdue": 4, "asset_health": 52, "asset_age": 15,
                     "traffic_density": 0.55, "historical_failures": 5, "failure_consequence": 0.7,
                     "operational_criticality": 0.68},
    },
    {
        "id": "M008", "asset": "Signal S-201", "department": "S&T", "section": "S3",
        "work": "Point machine repair", "duration": 55, "required_crew": "S&T crew",
        "required_equipment": "Testing equipment", "preferred_start": hm(2, 0), "preferred_end": hm(4, 0),
        "features": {"severity": 5, "days_overdue": 6, "asset_health": 35, "asset_age": 19,
                     "traffic_density": 0.75, "historical_failures": 7, "failure_consequence": 0.85,
                     "operational_criticality": 0.82},
    },
    {
        "id": "M009", "asset": "OHE O-33", "department": "TRD", "section": "S3",
        "work": "OHE tensioning", "duration": 40, "required_crew": "TRD crew",
        "required_equipment": "OHE equipment", "preferred_start": hm(2, 30), "preferred_end": hm(5, 0),
        "features": {"severity": 3, "days_overdue": 1, "asset_health": 72, "asset_age": 9,
                     "traffic_density": 0.5, "historical_failures": 2, "failure_consequence": 0.42,
                     "operational_criticality": 0.42},
    },
    {
        "id": "M010", "asset": "Track T3-51", "department": "Engineering", "section": "S2",
        "work": "Rail grinding", "duration": 60, "required_crew": "Engineering crew",
        "required_equipment": "Grinding machine", "preferred_start": hm(2, 0), "preferred_end": hm(5, 0),
        "features": {"severity": 1, "days_overdue": 0, "asset_health": 91, "asset_age": 4,
                     "traffic_density": 0.5, "historical_failures": 0, "failure_consequence": 0.2,
                     "operational_criticality": 0.2},
    },
    {
        "id": "M011", "asset": "Signal S-305", "department": "S&T", "section": "S1",
        "work": "Cable fault repair", "duration": 35, "required_crew": "S&T crew",
        "required_equipment": "Testing equipment", "preferred_start": hm(1, 30), "preferred_end": hm(4, 0),
        "features": {"severity": 4, "days_overdue": 3, "asset_health": 56, "asset_age": 13,
                     "traffic_density": 0.5, "historical_failures": 4, "failure_consequence": 0.68,
                     "operational_criticality": 0.65},
    },
    {
        "id": "M012", "asset": "OHE O-51", "department": "TRD", "section": "S2",
        "work": "Insulator wear check", "duration": 30, "required_crew": "TRD crew",
        "required_equipment": "OHE equipment", "preferred_start": hm(2, 30), "preferred_end": hm(5, 0),
        "features": {"severity": 1, "days_overdue": 0, "asset_health": 92, "asset_age": 3,
                     "traffic_density": 0.5, "historical_failures": 0, "failure_consequence": 0.18,
                     "operational_criticality": 0.2},
    },
    {
        "id": "M013", "asset": "Track T2-09", "department": "Engineering", "section": "S1",
        "work": "Formation repair", "duration": 120, "required_crew": "Engineering crew",
        "required_equipment": "Excavator", "preferred_start": hm(1, 0), "preferred_end": hm(4, 0),
        "features": {"severity": 3, "days_overdue": 2, "asset_health": 66, "asset_age": 12,
                     "traffic_density": 0.45, "historical_failures": 2, "failure_consequence": 0.46,
                     "operational_criticality": 0.46},
    },
    {
        "id": "M014", "asset": "Signal S-410", "department": "S&T", "section": "S3",
        "work": "Interlocking test", "duration": 45, "required_crew": "S&T crew",
        "required_equipment": "Testing equipment", "preferred_start": hm(2, 0), "preferred_end": hm(4, 0),
        "features": {"severity": 2, "days_overdue": 1, "asset_health": 74, "asset_age": 8,
                     "traffic_density": 0.5, "historical_failures": 1, "failure_consequence": 0.4,
                     "operational_criticality": 0.4},
    },
    {
        "id": "M015", "asset": "OHE O-77", "department": "TRD", "section": "S1",
        "work": "OHE inspection", "duration": 35, "required_crew": "TRD crew",
        "required_equipment": "OHE equipment", "preferred_start": hm(2, 30), "preferred_end": hm(5, 0),
        "features": {"severity": 1, "days_overdue": 0, "asset_health": 93, "asset_age": 3,
                     "traffic_density": 0.35, "historical_failures": 0, "failure_consequence": 0.15,
                     "operational_criticality": 0.18},
    },
]


def default_conditions() -> dict:
    """Baseline operating conditions. Mutated in-memory by /api/reoptimize."""
    return {
        "block_window": {"start": hm(2, 0), "end": hm(5, 0)},
        "crew_windows": {
            "Engineering": {"start": hm(1, 30), "end": hm(4, 30)},
            "S&T": {"start": hm(2, 0), "end": hm(4, 20)},
            "TRD": {"start": hm(2, 30), "end": hm(5, 0)},
        },
        "high_priority_trains": list(HIGH_PRIORITY_TRAINS),
        "train_delays": {},  # train number -> minutes added to entry/exit
    }
