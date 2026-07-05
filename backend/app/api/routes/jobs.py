from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_export_service, get_job_service
from app.database.session import get_session
from app.schemas.businesses import BusinessRead
from app.schemas.exports import ExportRequest, ExportResponse
from app.schemas.jobs import JobCreateRequest, JobCreateResponse, JobRead
from app.services.export_service import ExportService
from app.services.job_service import JobService

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("", response_model=JobCreateResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_job(
    payload: JobCreateRequest,
    session: AsyncSession = Depends(get_session),
    service: JobService = Depends(get_job_service),
) -> JobCreateResponse:
    job = await service.create_job(session, payload)
    return JobCreateResponse(job_id=job.id, status=job.status.value, query=job.query)


@router.get("/{job_id}", response_model=JobRead)
async def read_job(job_id: int, session: AsyncSession = Depends(get_session), service: JobService = Depends(get_job_service)) -> JobRead:
    job = await service.get_job(session, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobRead.model_validate(job, from_attributes=True)


@router.get("/{job_id}/businesses", response_model=list[BusinessRead])
async def list_businesses(job_id: int, session: AsyncSession = Depends(get_session), service: JobService = Depends(get_job_service)) -> list[BusinessRead]:
    businesses = await service.list_businesses(session, job_id)
    return [BusinessRead.model_validate(business, from_attributes=True) for business in businesses]


@router.post("/{job_id}/exports", response_model=ExportResponse)
async def export_results(job_id: int, payload: ExportRequest, session: AsyncSession = Depends(get_session), service: ExportService = Depends(get_export_service)) -> ExportResponse:
    rows = await service.build_rows(session, job_id)
    if payload.format == "csv":
        return ExportResponse(job_id=job_id, format="csv", message=f"Ready with {len(rows)} rows")
    if payload.format == "excel":
        return ExportResponse(job_id=job_id, format="excel", message=f"Ready with {len(rows)} rows")
    if payload.format == "google_sheets":
        return ExportResponse(job_id=job_id, format="google_sheets", message="Google Sheets integration requires credentials and a connector implementation")
    raise HTTPException(status_code=400, detail="Unsupported export format")


@router.get("/{job_id}/exports/{format_name}")
async def download_export(
    job_id: int,
    format_name: str,
    session: AsyncSession = Depends(get_session),
    service: ExportService = Depends(get_export_service),
) -> Response:
    rows = await service.build_rows(session, job_id)
    if format_name == "csv":
        content = service.to_csv(rows)
        return Response(content=content, media_type="text/csv", headers={"Content-Disposition": f'attachment; filename="job-{job_id}.csv"'})
    if format_name == "excel":
        content = service.to_excel(rows)
        return Response(
            content=content,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="job-{job_id}.xlsx"'},
        )
    raise HTTPException(status_code=400, detail="Unsupported export format")
