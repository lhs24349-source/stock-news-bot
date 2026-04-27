"""
스케줄 관리 API.

4가지 스케줄 모드(Backfill, Interval, Digest, Event)의
CRUD 및 수동 실행을 제공합니다.
"""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.schedule import ScheduleConfig
from app.scheduler.engine import (
    add_cron_job,
    add_interval_job,
    list_jobs,
    remove_job,
    get_scheduler,
)
from app.scheduler.jobs import run_news_pipeline, run_digest_pipeline
from app.schemas.schedule import (
    ScheduleCreate,
    ScheduleResponse,
    ScheduleUpdate,
)

router = APIRouter(prefix="/api/schedule", tags=["스케줄"])


@router.get("", summary="스케줄 목록", response_model=list[ScheduleResponse])
async def list_schedules(
    db: AsyncSession = Depends(get_db),
) -> list[ScheduleResponse]:
    """모든 스케줄 설정을 조회합니다."""
    stmt = select(ScheduleConfig).order_by(ScheduleConfig.created_at.desc())
    result = await db.execute(stmt)
    schedules = result.scalars().all()

    responses = []
    for s in schedules:
        responses.append(ScheduleResponse(
            id=s.id,
            name=s.name,
            schedule_type=s.schedule_type,
            config=json.loads(s.config_json),
            keyword_group_ids=(
                [int(x) for x in s.keyword_group_ids.split(",") if x.strip()]
                if s.keyword_group_ids else []
            ),
            is_active=s.is_active,
            last_run_at=s.last_run_at,
            next_run_at=s.next_run_at,
            created_at=s.created_at,
        ))
    return responses


@router.post(
    "", summary="스케줄 생성", response_model=ScheduleResponse, status_code=201
)
async def create_schedule(
    body: ScheduleCreate,
    db: AsyncSession = Depends(get_db),
) -> ScheduleResponse:
    """새 스케줄을 생성하고 APScheduler에 등록합니다."""
    schedule = ScheduleConfig(
        name=body.name,
        schedule_type=body.schedule_type,
        config_json=json.dumps(body.config, ensure_ascii=False),
        keyword_group_ids=(
            ",".join(str(x) for x in body.keyword_group_ids)
            if body.keyword_group_ids else None
        ),
    )
    db.add(schedule)
    await db.flush()
    await db.refresh(schedule)

    # APScheduler에 작업 등록
    if body.schedule_type == "interval":
        from app.scheduler.jobs import run_news_pipeline
        add_interval_job(
            job_id=f"schedule_{schedule.id}",
            func=run_news_pipeline,
            minutes=body.config.get("minutes", 60),
            send_notification=True,
        )
    elif body.schedule_type == "interval_silent":
        from app.scheduler.jobs import run_news_pipeline
        add_interval_job(
            job_id=f"schedule_{schedule.id}",
            func=run_news_pipeline,
            minutes=body.config.get("minutes", 60),
            send_notification=False,
        )
    elif body.schedule_type == "digest":
        from app.scheduler.jobs import run_news_pipeline
        cron_expr = body.config.get("cron_expression", body.config.get("cron", "0 18 * * *"))
        add_cron_job(
            job_id=f"schedule_{schedule.id}",
            func=run_news_pipeline,
            cron_expression=cron_expr,
            hours=24,
            send_notification=True,
        )
    elif body.schedule_type == "window_digest":
        from app.scheduler.jobs import run_news_pipeline, run_digest_pipeline
        start_hour = int(body.config.get("start_hour", 3))
        end_hour = int(body.config.get("end_hour", 7))
        interval = int(body.config.get("interval_minutes", 10))

        # 자정을 넘기는 시간대 처리 (예: 22시 ~ 2시)
        if start_hour < end_hour:
            hour_range = f"{start_hour}-{end_hour - 1}"
            duration = end_hour - start_hour
        else:
            hour_range = f"{start_hour}-23,0-{end_hour - 1}"
            duration = (24 - start_hour) + end_hour

        # 1. 조용한 수집기 등록 (알림X)
        add_cron_job(
            job_id=f"schedule_{schedule.id}_collect",
            func=run_news_pipeline,
            cron_expression=f"*/{interval} {hour_range} * * *",
            hours=1,
            send_notification=False,
        )
        
        # 2. 요약 알림 전송기 등록 (알림O)
        add_cron_job(
            job_id=f"schedule_{schedule.id}_digest",
            func=run_digest_pipeline,
            cron_expression=f"0 {end_hour} * * *",
            hours=duration,
        )

    return ScheduleResponse(
        id=schedule.id,
        name=schedule.name,
        schedule_type=schedule.schedule_type,
        config=body.config,
        keyword_group_ids=body.keyword_group_ids,
        is_active=schedule.is_active,
        last_run_at=schedule.last_run_at,
        next_run_at=schedule.next_run_at,
        created_at=schedule.created_at,
    )


@router.delete("/{schedule_id}", summary="스케줄 삭제", status_code=204)
async def delete_schedule(
    schedule_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """스케줄을 삭제하고 APScheduler에서 제거합니다."""
    stmt = select(ScheduleConfig).where(ScheduleConfig.id == schedule_id)
    result = await db.execute(stmt)
    schedule = result.scalar_one_or_none()

    if not schedule:
        raise HTTPException(status_code=404, detail="스케줄을 찾을 수 없습니다")

    remove_job(f"schedule_{schedule_id}")
    remove_job(f"schedule_{schedule_id}_collect")
    remove_job(f"schedule_{schedule_id}_digest")
    await db.delete(schedule)


@router.post(
    "/{schedule_id}/run",
    summary="스케줄 수동 즉시 실행",
    description="등록된 스케줄의 작업을 즉시 1회 실행합니다.",
)
async def run_schedule_now(
    schedule_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """스케줄에 설정된 작업을 즉시 수동 실행합니다."""
    import asyncio
    from datetime import datetime, timezone

    stmt = select(ScheduleConfig).where(ScheduleConfig.id == schedule_id)
    result = await db.execute(stmt)
    schedule = result.scalar_one_or_none()

    if not schedule:
        raise HTTPException(status_code=404, detail="스케줄을 찾을 수 없습니다")

    config = json.loads(schedule.config_json)

    # 스케줄 타입에 따라 적절한 파이프라인 실행
    if schedule.schedule_type in ("interval", "interval_silent", "backfill"):
        pipeline_result = await run_news_pipeline(
            hours=config.get("hours", 24),
            send_notification=(schedule.schedule_type != "interval_silent"),
        )
    elif schedule.schedule_type == "digest":
        pipeline_result = await run_news_pipeline(
            hours=24,
            send_notification=True,
        )
    elif schedule.schedule_type == "window_digest":
        # window_digest는 수동 실행 시 현재 시점 기준으로 수집+알림
        duration = int(config.get("end_hour", 7)) - int(config.get("start_hour", 3))
        if duration <= 0:
            duration += 24
        pipeline_result = await run_news_pipeline(
            hours=duration,
            send_notification=True,
        )
    else:
        pipeline_result = await run_news_pipeline(
            hours=24,
            send_notification=True,
        )

    # 마지막 실행 시각 갱신
    schedule.last_run_at = datetime.now(timezone.utc)
    await db.commit()

    return {
        "message": f"스케줄 '{schedule.name}' 수동 실행 완료",
        "result": pipeline_result,
    }


@router.get("/jobs", summary="실행 중인 작업 목록")
async def get_running_jobs() -> list[dict]:
    """APScheduler에 등록된 모든 작업 목록을 반환합니다."""
    return list_jobs()
