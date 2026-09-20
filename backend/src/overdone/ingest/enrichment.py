from __future__ import annotations

import json
from typing import Any

from overdone.config import settings

_JOINTS = ("shoulder", "knee", "spine", "elbow")
_PRESS_MUSCLES = {"chest", "shoulders", "triceps"}
_KNEE_MUSCLES = {"quadriceps", "quads", "glutes", "gluteus maximus"}
_AXIAL_IDS = ("squat", "deadlift", "good-morning", "good_morning")


def as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def load_rules() -> dict[str, Any]:
    path = settings.resolved_enrichment_rules_path()
    if not path.exists():
        return {"aliases": {}, "by_source_id": {}, "defaults": {}}
    return json.loads(path.read_text())


def enrichment_for(exercise: dict[str, Any], rules: dict[str, Any]) -> dict[str, Any]:
    source_id = str(exercise.get("id") or exercise.get("source_id") or "")
    name = str(exercise.get("name") or "").casefold()
    mechanic = str(exercise.get("mechanic") or "").casefold()
    category = str(exercise.get("category") or "").casefold()
    primary = [
        m.casefold()
        for m in as_list(
            exercise.get("primaryMuscles") or exercise.get("primary_muscles")
        )
    ]
    secondary = [
        m.casefold()
        for m in as_list(
            exercise.get("secondaryMuscles") or exercise.get("secondary_muscles")
        )
    ]
    muscles = set(primary + secondary)
    defaults = rules.get("defaults") or {}
    overlay = (rules.get("by_source_id") or {}).get(source_id, {})

    axial = float(overlay.get("axial_factor", defaults.get("axial_factor", 0.15)))
    if any(token in source_id.casefold() or token in name for token in _AXIAL_IDS):
        axial = float(overlay.get("axial_factor", 0.9))
    elif "lower back" in muscles or "hinge" in mechanic:
        axial = float(overlay.get("axial_factor", 0.6))

    if mechanic == "compound":
        cns = 0.85
    elif category in {"olympic weightlifting", "strongman", "olympic"}:
        cns = 0.5
    else:
        cns = 0.25
    cns = float(overlay.get("cns_factor", cns))

    joints = {
        "shoulder": 0.0,
        "knee": 0.0,
        "spine": axial,
        "elbow": 0.0,
    }
    if muscles & _PRESS_MUSCLES or "press" in name:
        joints["shoulder"] = (
            0.7 if "chest" in primary or "shoulders" in primary else 0.4
        )
        joints["elbow"] = 0.35
    if muscles & _KNEE_MUSCLES or "squat" in name or "lunge" in name:
        joints["knee"] = 0.7
    for key in _JOINTS:
        if key in overlay.get("joints", {}):
            joints[key] = float(overlay["joints"][key])
    return {"axial_factor": axial, "cns_factor": cns, "joints": joints}


def chunk_text(exercise: dict[str, Any], factors: dict[str, Any]) -> str:
    name = exercise.get("name") or ""
    muscles = ", ".join(
        as_list(exercise.get("primaryMuscles") or exercise.get("primary_muscles"))
    )
    instructions = " ".join(as_list(exercise.get("instructions")))
    blurb = (
        f"axial_factor={factors['axial_factor']} "
        f"cns_factor={factors['cns_factor']} joints={factors['joints']}"
    )
    return f"{name}. Muscles: {muscles}. {instructions} {blurb}".strip()
