from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from overdone.models.user_log import UserBenchmark, UserSession, UserSettings
from overdone.schemas.dto import ExtractedPrompt, LogSet, ProposedItem, Unit
from overdone.services.units import to_kg


async def load_history(
    session: AsyncSession,
) -> tuple[list[UserSession], list[UserBenchmark], str]:
    settings = await session.get(UserSettings, 1)
    preferred = settings.preferred_unit if settings else "lb"
    sessions = list(
        (
            await session.scalars(
                select(UserSession)
                .options(selectinload(UserSession.sets))
                .order_by(UserSession.logged_on.desc(), UserSession.id.desc())
            )
        ).all()
    )
    benchmarks = list(
        (await session.scalars(select(UserBenchmark).order_by(UserBenchmark.id))).all()
    )
    return sessions, benchmarks, preferred


def stored_units(
    sessions: list[UserSession], benchmarks: list[UserBenchmark]
) -> set[str]:
    units = {row.unit for row in benchmarks}
    for logged in sessions:
        for item in logged.sets:
            units.add(item.unit)
    return units


def baseline_names(
    sessions: list[UserSession], benchmarks: list[UserBenchmark]
) -> list[str]:
    names: list[str] = []
    seen: set[str] = set()
    for logged in sessions:
        for item in logged.sets:
            if item.exercise_name not in seen:
                names.append(item.exercise_name)
                seen.add(item.exercise_name)
    for row in benchmarks:
        if row.exercise_name not in seen:
            names.append(row.exercise_name)
            seen.add(row.exercise_name)
    return names


def inherit_unit(extracted: ExtractedPrompt, unit: Unit) -> ExtractedPrompt:
    if extracted.unit is not None:
        return extracted
    items: list[ProposedItem] = []
    for item in extracted.items:
        delta = to_kg(item.delta_kg, unit.value) if item.delta_kg is not None else None
        weight = (
            to_kg(item.weight_kg, unit.value) if item.weight_kg is not None else None
        )
        items.append(item.model_copy(update={"delta_kg": delta, "weight_kg": weight}))
    target = (
        to_kg(extracted.target_weight_kg, unit.value)
        if extracted.target_weight_kg is not None
        else None
    )
    return extracted.model_copy(
        update={"items": items, "target_weight_kg": target, "unit": unit}
    )


def last_working(
    names: set[str], sessions: list[UserSession], benchmarks: list[UserBenchmark]
) -> LogSet | None:
    folded = {name.casefold() for name in names if name}
    for logged in sessions:
        matching = [
            row for row in logged.sets if row.exercise_name.casefold() in folded
        ]
        if matching:
            heaviest = max(matching, key=lambda row: row.weight_kg)
            return LogSet(
                exercise_id=heaviest.exercise_name,
                exercise_name=heaviest.exercise_name,
                weight_kg=heaviest.weight_kg,
                reps=heaviest.reps,
                sets=heaviest.sets,
            )
    for row in benchmarks:
        if row.exercise_name.casefold() in folded:
            return LogSet(
                exercise_id=row.exercise_name,
                exercise_name=row.exercise_name,
                weight_kg=0.80 * row.one_rm_kg,
                reps=5,
                sets=3,
            )
    return None


def weekly_velocity(names: set[str], sessions: list[UserSession]) -> float:
    folded = {name.casefold() for name in names if name}
    points: list[tuple[date, float]] = []
    chronological = list(reversed(sessions))
    for logged in chronological:
        matching = [
            row for row in logged.sets if row.exercise_name.casefold() in folded
        ]
        if matching:
            points.append((logged.logged_on, max(row.weight_kg for row in matching)))
    points = points[-8:]
    if len(points) < 2:
        return 0.0
    days = (points[-1][0] - points[0][0]).days
    if days <= 0:
        return 0.0
    return (points[-1][1] - points[0][1]) / (days / 7.0)
