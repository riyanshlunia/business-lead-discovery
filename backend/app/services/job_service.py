from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.entities import Business, Job, JobStatus, Project, User
from app.schemas.jobs import JobCreateRequest


class JobService:
    async def create_job(self, session: AsyncSession, request: JobCreateRequest) -> Job:
        user = await self._get_or_create_default_user(session)
        project = await self._get_or_create_project(session, user.id, request)

        query = f"{request.industry} in {request.location}"

        job = Job(
            project_id=project.id,
            status=JobStatus.queued,
            industry=request.industry,
            location=request.location,
            query=query,
            target_limit=request.limit,
        )

        session.add(job)
        await session.flush()
        await session.commit()
        await session.refresh(job)
        
        return job

    async def get_job(self, session: AsyncSession, job_id: int) -> Job | None:
        return await session.get(Job, job_id)

    async def list_businesses(self, session: AsyncSession, job_id: int) -> list[Business]:
        statement = (
            select(Business)
            .where(Business.job_id == job_id)
            .order_by(Business.id.asc())
            .options(
                selectinload(Business.emails),
                selectinload(Business.social_accounts),
                selectinload(Business.website_record),
                selectinload(Business.lead_score),
            )
        )
        result = await session.execute(statement)
        return list(result.scalars().unique().all())

    async def set_job_status(
        self,
        session: AsyncSession,
        job_id: int,
        status: JobStatus,
        error_message: str | None = None,
    ) -> None:
        job = await session.get(Job, job_id)
        if job is None:
            return

        job.status = status

        if status == JobStatus.running and job.started_at is None:
            job.started_at = datetime.now(timezone.utc)

        if status in {JobStatus.completed, JobStatus.failed}:
            job.finished_at = datetime.now(timezone.utc)

        job.error_message = error_message

        await session.commit()

    async def _get_or_create_default_user(self, session: AsyncSession) -> User:
        statement = select(User).where(User.email == "system@leadgen.local")
        result = await session.execute(statement)
        user = result.scalar_one_or_none()

        if user:
            return user

        user = User(
            email="system@leadgen.local",
            full_name="System",
        )

        session.add(user)
        await session.commit()
        await session.refresh(user)

        return user

    async def _get_or_create_project(
        self,
        session: AsyncSession,
        user_id: int,
        request: JobCreateRequest,
    ) -> Project:
        project_name = request.project_name or f"{request.industry} - {request.location}"

        statement = select(Project).where(
            Project.user_id == user_id,
            Project.name == project_name,
        )

        result = await session.execute(statement)
        project = result.scalar_one_or_none()

        if project:
            return project

        project = Project(
            user_id=user_id,
            name=project_name,
            industry=request.industry,
            location=request.location,
        )

        session.add(project)
        await session.commit()
        await session.refresh(project)

        return project