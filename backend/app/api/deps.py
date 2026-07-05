from app.services.export_service import ExportService
from app.services.job_service import JobService


def get_job_service() -> JobService:
    return JobService()


def get_export_service() -> ExportService:
    return ExportService()
