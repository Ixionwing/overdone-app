from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from overdone.models.base import Base


class Exercise(Base):
    __tablename__ = "exercises"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[str] = mapped_column(String(255), unique=True)
    name: Mapped[str] = mapped_column(String(255))
    force: Mapped[str | None] = mapped_column(String(64), nullable=True)
    level: Mapped[str | None] = mapped_column(String(64), nullable=True)
    mechanic: Mapped[str | None] = mapped_column(String(64), nullable=True)
    equipment: Mapped[str | None] = mapped_column(String(64), nullable=True)
    category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    primary_muscles: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    secondary_muscles: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    instructions: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)

    enrichment: Mapped["ExerciseEnrichment | None"] = relationship(
        back_populates="exercise", lazy="raise"
    )
    aliases: Mapped[list["ExerciseAlias"]] = relationship(
        back_populates="exercise", lazy="raise"
    )


class ExerciseEnrichment(Base):
    __tablename__ = "exercise_enrichment"

    exercise_id: Mapped[int] = mapped_column(
        ForeignKey("exercises.id", ondelete="CASCADE"), primary_key=True
    )
    axial_factor: Mapped[float]
    cns_factor: Mapped[float]
    joints: Mapped[dict[str, float]] = mapped_column(JSONB)

    exercise: Mapped[Exercise] = relationship(back_populates="enrichment", lazy="raise")


class ExerciseAlias(Base):
    __tablename__ = "exercise_aliases"

    id: Mapped[int] = mapped_column(primary_key=True)
    exercise_id: Mapped[int] = mapped_column(
        ForeignKey("exercises.id", ondelete="CASCADE")
    )
    alias: Mapped[str] = mapped_column(String(255), unique=True)

    exercise: Mapped[Exercise] = relationship(back_populates="aliases", lazy="raise")
