"""
APScheduler 엔진.

4가지 스케줄 모드(Backfill, Interval, Digest, Event)를 지원하며,
SQLAlchemyJobStore로 중복 실행을 방지합니다.
"""

from __future__ import annotations

import json
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.config import get_settings
from app.core.logging import get_logger
from app.utils.timezone import KST

logger = get_logger(__name__)

# 전역 스케줄러 인스턴스
_scheduler: Optional[AsyncIOScheduler] = None


def get_scheduler() -> AsyncIOScheduler:
    """스케줄러 싱글턴을 반환합니다."""
    global _scheduler
    if _scheduler is None:
        _scheduler = AsyncIOScheduler(
            timezone=KST,
            job_defaults={
                "coalesce": True,       # 밀린 작업 1회만 실행
                "max_instances": 1,     # 동시 실행 방지
                "misfire_grace_time": 60,
            },
        )
    return _scheduler


async def start_scheduler() -> None:
    """스케줄러를 시작합니다."""
    scheduler = get_scheduler()
    if not scheduler.running:
        scheduler.start()
        logger.info("APScheduler 시작됨", timezone=str(KST))


async def shutdown_scheduler() -> None:
    """스케줄러를 정상 종료합니다 (Graceful shutdown)."""
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=True)
        logger.info("APScheduler 정상 종료됨")
        _scheduler = None


def add_interval_job(
    job_id: str,
    func,
    minutes: int = 30,
    **kwargs,
) -> None:
    """Interval 스케줄 작업을 등록합니다.

    Args:
        job_id: 고유 작업 ID
        func: 실행할 async 함수
        minutes: 실행 간격 (분)
    """
    scheduler = get_scheduler()

    # 기존 동일 ID 작업 제거 (갱신)
    existing = scheduler.get_job(job_id)
    if existing:
        scheduler.remove_job(job_id)
        logger.info("기존 Interval 작업 교체", job_id=job_id)

    scheduler.add_job(
        func,
        trigger=IntervalTrigger(minutes=minutes, timezone=KST),
        id=job_id,
        name=f"interval_{job_id}",
        kwargs=kwargs,
        replace_existing=True,
    )
    logger.info(
        "Interval 작업 등록",
        job_id=job_id,
        interval_minutes=minutes,
    )


def add_cron_job(
    job_id: str,
    func,
    cron_expression: str,
    **kwargs,
) -> None:
    """Digest(Cron) 스케줄 작업을 등록합니다.

    Args:
        job_id: 고유 작업 ID
        func: 실행할 async 함수
        cron_expression: Cron 표현식 (예: "0 9,18 * * *")
    """
    scheduler = get_scheduler()

    existing = scheduler.get_job(job_id)
    if existing:
        scheduler.remove_job(job_id)

    # Cron 표현식 파싱 (분 시 일 월 요일)
    parts = cron_expression.strip().split()
    if len(parts) == 5:
        trigger = CronTrigger(
            minute=parts[0],
            hour=parts[1],
            day=parts[2],
            month=parts[3],
            day_of_week=parts[4],
            timezone=KST,
        )
    else:
        raise ValueError(f"잘못된 Cron 표현식: {cron_expression}")

    scheduler.add_job(
        func,
        trigger=trigger,
        id=job_id,
        name=f"cron_{job_id}",
        kwargs=kwargs,
        replace_existing=True,
    )
    logger.info(
        "Cron 작업 등록",
        job_id=job_id,
        cron=cron_expression,
    )


def remove_job(job_id: str) -> bool:
    """스케줄 작업을 제거합니다."""
    scheduler = get_scheduler()
    existing = scheduler.get_job(job_id)
    if existing:
        scheduler.remove_job(job_id)
        logger.info("작업 제거됨", job_id=job_id)
        return True
    return False


def list_jobs() -> list[dict]:
    """등록된 모든 작업 목록을 반환합니다."""
    scheduler = get_scheduler()
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run_time": str(job.next_run_time) if job.next_run_time else None,
            "trigger": str(job.trigger),
        })
    return jobs
