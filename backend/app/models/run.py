from datetime import datetime, timezone
from sqlalchemy import String, Text, Float, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.db import Base


def _now():
    return datetime.now(timezone.utc)


class Run(Base):
    __tablename__ = "runs"
    run_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    sandbox_name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    problem_id: Mapped[str] = mapped_column(String(64), nullable=False)
    state: Mapped[str] = mapped_column(String(16), nullable=False)
    execution_target: Mapped[str] = mapped_column(String(32), nullable=False)
    task_description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    wall_clock_s: Mapped[float | None] = mapped_column(Float)
    boot_to_ready_s: Mapped[float | None] = mapped_column(Float)
    cost_usd: Mapped[float | None] = mapped_column(Float)
    result_summary: Mapped[str | None] = mapped_column(Text)
    error_details: Mapped[str | None] = mapped_column(Text)
    cleanup_status: Mapped[str | None] = mapped_column(String(32))
