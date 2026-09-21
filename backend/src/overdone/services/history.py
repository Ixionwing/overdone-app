from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import date
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from overdone.models.user_log import UserBenchmark, UserSession, UserSettings
from overdone.schemas.api import BaselineImport
from overdone.schemas.dto import ExtractedPrompt, LogSet, ProposedItem, Unit
from overdone.services.units import to_kg


@dataclass
class MemorySet:
    exercise_name: str
    weight_kg: float
    reps: int
    sets: int
    unit: str


@dataclass
class MemorySession:
    logged_on: date
    notes: str | None = None
    sets: list[MemorySet] = field(default_factory=list)


@dataclass
class MemoryBenchmark:
    exercise_name: str
    one_rm_kg: float
    unit: str


def history_from_import(
    payload: BaselineImport,
) -> tuple[list[MemorySession], list[MemoryBenchmark], str]:
    preferred = payload.preferred_unit
    sessions = [
        MemorySession(
            logged_on=logged.date,
            notes=logged.notes,
            sets=[
                MemorySet(
                    exercise_name=item.exercise,
                    weight_kg=to_kg(item.weight, (item.unit or preferred).lower()),
                    reps=item.reps,
                    sets=item.sets,
                    unit=(item.unit or preferred).lower(),
                )
                for item in logged.sets
            ],
        )
        for logged in payload.sessions
    ]
    sessions.sort(key=lambda row: row.logged_on, reverse=True)
    benchmarks = [
        MemoryBenchmark(
            exercise_name=row.exercise,
            one_rm_kg=to_kg(row.one_rm, (row.unit or preferred).lower()),
            unit=(row.unit or preferred).lower(),
        )
        for row in payload.benchmarks
    ]
    return sessions, benchmarks, preferred


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


def stored_units(sessions: Sequence[Any], benchmarks: Sequence[Any]) -> set[str]:
    units = {row.unit for row in benchmarks}
    for logged in sessions:
        for item in logged.sets:
            units.add(item.unit)
    return units


def baseline_names(sessions: Sequence[Any], benchmarks: Sequence[Any]) -> list[str]:
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
    names: set[str],
    sessions: Sequence[Any],
    benchmarks: Sequence[Any],
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


def weekly_velocity(names: set[str], sessions: Sequence[Any]) -> float:
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
