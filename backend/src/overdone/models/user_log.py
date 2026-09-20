from datetime import date

from sqlalchemy import CheckConstraint, Date, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from overdone.models.base import Base


class UserSettings(Base):
    __tablename__ = "user_settings"
    __table_args__ = (
        CheckConstraint("preferred_unit IN ('lb', 'kg')", name="preferred_unit"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    preferred_unit: Mapped[str] = mapped_column(String(2), default="lb")


class UserBenchmark(Base):
    __tablename__ = "user_benchmarks"
    __table_args__ = (CheckConstraint("unit IN ('lb', 'kg')", name="unit"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    exercise_id: Mapped[int | None] = mapped_column(
        ForeignKey("exercises.id", ondelete="SET NULL"), nullable=True
    )
    exercise_name: Mapped[str] = mapped_column(String(255))
    one_rm_kg: Mapped[float]
    unit: Mapped[str] = mapped_column(String(2))


class UserSession(Base):
    __tablename__ = "user_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    logged_on: Mapped[date] = mapped_column(Date)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    sets: Mapped[list["UserSet"]] = relationship(
        back_populates="session", lazy="raise", cascade="all, delete-orphan"
    )


class UserSet(Base):
    __tablename__ = "user_sets"
    __table_args__ = (CheckConstraint("unit IN ('lb', 'kg')", name="unit"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("user_sessions.id", ondelete="CASCADE")
    )
    exercise_id: Mapped[int | None] = mapped_column(
        ForeignKey("exercises.id", ondelete="SET NULL"), nullable=True
    )
    exercise_name: Mapped[str] = mapped_column(String(255))
    weight_kg: Mapped[float]
    unit: Mapped[str] = mapped_column(String(2))
    reps: Mapped[int]
    sets: Mapped[int] = mapped_column(Integer, default=1)

    session: Mapped[UserSession] = relationship(back_populates="sets", lazy="raise")
