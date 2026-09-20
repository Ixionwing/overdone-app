from __future__ import annotations

import json
import re
from datetime import date

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from overdone.models.user_log import UserBenchmark, UserSession, UserSet, UserSettings
from overdone.schemas.api import (
    BaselineImport,
    BaselineStatus,
    ImportBenchmark,
    ImportSession,
    ImportSet,
)
from overdone.services.retrieve import rebuild_session_notes
from overdone.services.units import from_kg, to_kg

_DATE = re.compile(r"^(\d{4}-\d{2}-\d{2})\s*$")
_PREFERRED = re.compile(r"^preferred_unit:\s*(lb|kg)\s*$", re.I)
_ONE_RM = re.compile(r"^1RM\s+(.+):\s+([\d.]+)\s*(lb|kg)\s*$", re.I)
_NOTES = re.compile(r"^notes:\s*(.+)\s*$", re.I)
_SET = re.compile(
    r"^(.+?)\s+(\d+)x(\d+)\s+@\s+([\d.]+)(?:\s*(lb|kg))?\s*$",
    re.I,
)


def _row_unit(explicit: str | None, preferred: str) -> str:
    unit = (explicit or preferred).lower()
    if unit not in {"lb", "kg"}:
        raise ValueError(f"unsupported unit: {unit}")
    return unit


async def replace_baseline(
    session: AsyncSession, payload: BaselineImport
) -> BaselineStatus:
    await session.execute(delete(UserSet))
    await session.execute(delete(UserSession))
    await session.execute(delete(UserBenchmark))
    await session.execute(delete(UserSettings))

    session.add(UserSettings(id=1, preferred_unit=payload.preferred_unit))
    for benchmark in payload.benchmarks:
        unit = _row_unit(benchmark.unit, payload.preferred_unit)
        session.add(
            UserBenchmark(
                exercise_name=benchmark.exercise,
                one_rm_kg=to_kg(benchmark.one_rm, unit),
                unit=unit,
            )
        )
    for logged in payload.sessions:
        row = UserSession(logged_on=logged.date, notes=logged.notes)
        session.add(row)
        await session.flush()
        for item in logged.sets:
            unit = _row_unit(item.unit, payload.preferred_unit)
            session.add(
                UserSet(
                    session_id=row.id,
                    exercise_name=item.exercise,
                    weight_kg=to_kg(item.weight, unit),
                    unit=unit,
                    reps=item.reps,
                    sets=item.sets,
                )
            )
    await session.flush()
    await rebuild_session_notes(session)
    return await get_baseline(session)


def parse_baseline_text(text: str) -> BaselineImport:
    stripped = text.strip()
    if stripped.startswith("{"):
        return BaselineImport.model_validate(json.loads(stripped))

    preferred = "lb"
    benchmarks: list[ImportBenchmark] = []
    sessions: list[ImportSession] = []
    current: ImportSession | None = None

    for raw_line in stripped.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if match := _PREFERRED.match(line):
            preferred = match.group(1).lower()
            continue
        if match := _ONE_RM.match(line):
            benchmarks.append(
                ImportBenchmark(
                    exercise=match.group(1).strip(),
                    one_rm=float(match.group(2)),
                    unit=match.group(3).lower(),
                )
            )
            continue
        if match := _DATE.match(line):
            current = ImportSession(date=date.fromisoformat(match.group(1)))
            sessions.append(current)
            continue
        if match := _NOTES.match(line):
            if current is None:
                raise ValueError("notes line before a session date")
            current.notes = match.group(1).strip()
            continue
        if match := _SET.match(line):
            if current is None:
                raise ValueError("set line before a session date")
            unit = match.group(5).lower() if match.group(5) else None
            current.sets.append(
                ImportSet(
                    exercise=match.group(1).strip(),
                    sets=int(match.group(2)),
                    reps=int(match.group(3)),
                    weight=float(match.group(4)),
                    unit=unit,
                )
            )
            continue
        raise ValueError(f"unrecognized baseline line: {line}")

    return BaselineImport(
        preferred_unit=preferred, benchmarks=benchmarks, sessions=sessions
    )


async def replace_baseline_from_text(
    session: AsyncSession, text: str
) -> BaselineStatus:
    return await replace_baseline(session, parse_baseline_text(text))


def _round_weight(value: float) -> float:
    return round(value, 4)


async def get_baseline(session: AsyncSession) -> BaselineStatus:
    settings = await session.get(UserSettings, 1)
    preferred = settings.preferred_unit if settings else "lb"

    benchmarks_result = await session.scalars(
        select(UserBenchmark).order_by(UserBenchmark.id)
    )
    sessions_result = await session.scalars(
        select(UserSession)
        .options(selectinload(UserSession.sets))
        .order_by(UserSession.logged_on)
    )

    benchmarks = [
        ImportBenchmark(
            exercise=row.exercise_name,
            one_rm=_round_weight(from_kg(row.one_rm_kg, row.unit)),
            unit=row.unit,
        )
        for row in benchmarks_result
    ]
    sessions = [
        ImportSession(
            date=row.logged_on,
            notes=row.notes,
            sets=[
                ImportSet(
                    exercise=item.exercise_name,
                    weight=_round_weight(from_kg(item.weight_kg, item.unit)),
                    reps=item.reps,
                    sets=item.sets,
                    unit=item.unit,
                )
                for item in sorted(row.sets, key=lambda item: item.id)
            ],
        )
        for row in sessions_result
    ]
    payload = BaselineImport(
        preferred_unit=preferred, benchmarks=benchmarks, sessions=sessions
    )
    set_count = await session.scalar(select(func.count()).select_from(UserSet)) or 0
    return BaselineStatus(
        preferred_unit=preferred,
        benchmark_count=len(benchmarks),
        session_count=len(sessions),
        set_count=int(set_count),
        baseline=payload,
    )
