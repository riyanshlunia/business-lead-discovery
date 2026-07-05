from pydantic import BaseModel


class ExportRequest(BaseModel):
    format: str


class ExportResponse(BaseModel):
    job_id: int
    format: str
    download_url: str | None = None
    message: str | None = None
