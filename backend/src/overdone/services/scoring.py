from overdone.schemas.dto import (
    DEFAULT_ENRICHMENT,
    ExerciseEnrichment,
    FactorScores,
    ItemVerdict,
    LogSet,
    ProposedItem,
    TrafficLight,
)

_RANK = {
    TrafficLight.green: 0,
    TrafficLight.yellow: 1,
    TrafficLight.red: 2,
}
_JOINTS = ("shoulder", "knee", "spine", "elbow")
# kg/week. With no dated progression, larger required rates are still red.
_UNKNOWN_VELOCITY_RED_KG = 1.5


def _worse(*lights: TrafficLight) -> TrafficLight:
    return max(lights, key=lambda light: _RANK[light])


def _pct_jump(new: float, old: float) -> float:
    if old == 0:
        if new == 0:
            return 0.0
        return 1000.0
    return (new - old) / old * 100.0


def _round(value: float) -> float:
    return round(value, 1)


def _light_from_volume(pct: float) -> TrafficLight:
    if pct < 10:
        return TrafficLight.green
    if pct <= 20:
        return TrafficLight.yellow
    return TrafficLight.red


def _light_from_cns_or_joint(pct: float) -> TrafficLight:
    if pct < 15:
        return TrafficLight.green
    if pct <= 30:
        return TrafficLight.yellow
    return TrafficLight.red


def _tonnage(weight_kg: float, reps: int, sets: int) -> float:
    return weight_kg * reps * sets


def fill_proposed(item: ProposedItem, last: LogSet) -> LogSet:
    if item.weight_kg is not None:
        weight = item.weight_kg
    elif item.delta_kg is not None:
        weight = last.weight_kg + item.delta_kg
    else:
        weight = last.weight_kg
    reps = item.reps if item.reps is not None else last.reps
    sets = item.sets if item.sets is not None else last.sets
    if item.extra_sets:
        sets += item.extra_sets
    return LogSet(
        exercise_id=item.exercise_id or last.exercise_id,
        exercise_name=item.exercise_name,
        weight_kg=weight,
        reps=reps,
        sets=sets,
    )


def _factors_for(
    proposed: LogSet, last: LogSet, enrichment: ExerciseEnrichment
) -> tuple[FactorScores, TrafficLight, float, float, float, dict[str, float]]:
    last_tonnage = _tonnage(last.weight_kg, last.reps, last.sets)
    proposed_tonnage = _tonnage(proposed.weight_kg, proposed.reps, proposed.sets)
    volume_pct = _pct_jump(proposed_tonnage, last_tonnage)
    last_axial = last_tonnage * enrichment.axial_factor
    last_cns = last_tonnage * enrichment.cns_factor
    axial = proposed_tonnage * enrichment.axial_factor
    cns = proposed_tonnage * enrichment.cns_factor
    joints = {
        name: proposed_tonnage * enrichment.joints.get(name, 0.0) for name in _JOINTS
    }
    last_joints = {
        name: last_tonnage * enrichment.joints.get(name, 0.0) for name in _JOINTS
    }
    axial_pct = _pct_jump(axial, last_axial)
    cns_pct = _pct_jump(cns, last_cns)
    joint_pcts = {name: _pct_jump(joints[name], last_joints[name]) for name in _JOINTS}
    light = _worse(
        _light_from_volume(volume_pct),
        _light_from_volume(axial_pct),
        _light_from_cns_or_joint(cns_pct),
        *(_light_from_cns_or_joint(pct) for pct in joint_pcts.values()),
    )
    return (
        FactorScores(
            volume_jump_pct=_round(volume_pct),
            axial_compression=_round(axial),
            cns_index=_round(cns),
            joint_vectors={name: _round(value) for name, value in joints.items()},
        ),
        light,
        volume_pct,
        axial_pct,
        cns_pct,
        joint_pcts,
    )


def score_session(
    items: list[ProposedItem],
    last_by_exercise: dict[str, LogSet],
    enrichment: dict[str, ExerciseEnrichment],
) -> tuple[TrafficLight, list[ItemVerdict], FactorScores]:
    verdicts: list[ItemVerdict] = []
    item_axial_pcts: list[float] = []
    item_cns_pcts: list[float] = []
    item_joint_pcts: list[dict[str, float]] = []
    last_tonnage_total = 0.0
    proposed_tonnage_total = 0.0
    last_axial_total = 0.0
    proposed_axial_total = 0.0
    last_cns_total = 0.0
    proposed_cns_total = 0.0
    last_joints_total = {name: 0.0 for name in _JOINTS}
    proposed_joints_total = {name: 0.0 for name in _JOINTS}

    for item in items:
        key = item.exercise_id or item.exercise_name
        last = last_by_exercise[key]
        enrich = enrichment.get(key, DEFAULT_ENRICHMENT)
        proposed = fill_proposed(item, last)
        factors, light, volume_pct, axial_pct, cns_pct, joint_pcts = _factors_for(
            proposed, last, enrich
        )
        last_t = _tonnage(last.weight_kg, last.reps, last.sets)
        prop_t = _tonnage(proposed.weight_kg, proposed.reps, proposed.sets)
        last_tonnage_total += last_t
        proposed_tonnage_total += prop_t
        last_axial_total += last_t * enrich.axial_factor
        proposed_axial_total += prop_t * enrich.axial_factor
        last_cns_total += last_t * enrich.cns_factor
        proposed_cns_total += prop_t * enrich.cns_factor
        for name in _JOINTS:
            last_joints_total[name] += last_t * enrich.joints.get(name, 0.0)
            proposed_joints_total[name] += prop_t * enrich.joints.get(name, 0.0)
        item_axial_pcts.append(axial_pct)
        item_cns_pcts.append(cns_pct)
        item_joint_pcts.append(joint_pcts)
        verdicts.append(
            ItemVerdict(
                exercise_id=key,
                exercise_name=item.exercise_name,
                light=light,
                factors=factors,
                narrative=(
                    f"{item.exercise_name} is {light.value}: volume jump "
                    f"{factors.volume_jump_pct:.1f}%."
                ),
            )
        )

    stacked_volume = _pct_jump(proposed_tonnage_total, last_tonnage_total)
    stacked_axial = max(
        _pct_jump(proposed_axial_total, last_axial_total),
        sum(item_axial_pcts),
    )
    stacked_cns = max(
        _pct_jump(proposed_cns_total, last_cns_total),
        sum(item_cns_pcts),
    )
    session_joints = {}
    session_joint_lights: list[TrafficLight] = []
    for name in _JOINTS:
        stacked = max(
            _pct_jump(proposed_joints_total[name], last_joints_total[name]),
            sum(pcts[name] for pcts in item_joint_pcts),
        )
        session_joints[name] = _round(proposed_joints_total[name])
        session_joint_lights.append(_light_from_cns_or_joint(stacked))

    session_factors = FactorScores(
        volume_jump_pct=_round(stacked_volume),
        axial_compression=_round(proposed_axial_total),
        cns_index=_round(proposed_cns_total),
        joint_vectors=session_joints,
    )
    if verdicts:
        item_worst = _worse(*(item.light for item in verdicts))
    else:
        item_worst = TrafficLight.green
    overall = _worse(
        item_worst,
        _light_from_volume(stacked_volume),
        _light_from_volume(stacked_axial),
        _light_from_cns_or_joint(stacked_cns),
        *session_joint_lights,
    )
    return overall, verdicts, session_factors


def score_macro(
    *,
    current_kg: float,
    target_kg: float,
    weeks: int,
    weekly_velocity_kg: float,
    working: LogSet,
    enrichment: ExerciseEnrichment,
    target_sets: int | None = None,
    target_reps: int | None = None,
) -> ItemVerdict:
    required_weekly = (target_kg - current_kg) / weeks if weeks else target_kg
    if weekly_velocity_kg <= 0:
        if required_weekly <= _UNKNOWN_VELOCITY_RED_KG:
            rate_light = TrafficLight.green
        else:
            rate_light = TrafficLight.red
    elif required_weekly <= 1.0 * weekly_velocity_kg:
        rate_light = TrafficLight.green
    elif required_weekly <= 1.5 * weekly_velocity_kg:
        rate_light = TrafficLight.yellow
    else:
        rate_light = TrafficLight.red
    sets = target_sets if target_sets is not None else working.sets
    reps = target_reps if target_reps is not None else working.reps
    target_item = ProposedItem(
        exercise_name=working.exercise_name,
        exercise_id=working.exercise_id,
        weight_kg=target_kg,
        reps=reps,
        sets=sets,
    )
    _overall, verdicts, _factors = score_session(
        [target_item],
        {working.exercise_id or working.exercise_name: working},
        {working.exercise_id or working.exercise_name: enrichment},
    )
    factors = verdicts[0].factors
    light = _worse(rate_light, verdicts[0].light)
    return ItemVerdict(
        exercise_id=working.exercise_id or working.exercise_name,
        exercise_name=working.exercise_name,
        light=light,
        factors=factors,
        narrative=f"{working.exercise_name} macro goal is {light.value}.",
    )
