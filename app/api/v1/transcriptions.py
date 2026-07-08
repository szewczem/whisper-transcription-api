from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import PlainTextResponse, Response

from app.api.dependencies import get_transcription_job_service
from app.api.v1.schemas.transcription import (
    CreateTranscriptionRequest,
    CreateTranscriptionResponse,
    TranscriptionStatusResponse,
)
from app.domain.transcription.job import TranscriptionJob, TranscriptionJobStatus
from app.services.transcription.job_service import TranscriptionJobService

router = APIRouter(
    tags=["transcriptions"],
)


@router.post(
    "/transcribe",
    response_model=CreateTranscriptionResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Create a transcription job",
)
def create_transcription_job(
    payload: CreateTranscriptionRequest,
    service: TranscriptionJobService = Depends(get_transcription_job_service),
) -> CreateTranscriptionResponse:
    job = service.create_job(
        audio_url=str(payload.audio_url),
        language=payload.language,
        webhook_url=(str(payload.webhook_url) if payload.webhook_url is not None else None),
    )

    return CreateTranscriptionResponse(
        job_id=job.id,
        status=job.status,
        message="Transcription job created successfully",
    )


@router.get(
    "/transcribe/{job_id}",
    response_model=TranscriptionStatusResponse,
    response_model_exclude_none=True,
    summary="Get transcription job status",
)
def get_transcription_job(
    job_id: UUID, service: TranscriptionJobService = Depends(get_transcription_job_service)
) -> TranscriptionStatusResponse:
    job = service.get_job(job_id)

    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transcription job not found.",
        )

    return _to_status_response(job)


@router.get("/transcribe/{job_id}/json")
def get_transcription_json_output(
    job_id: UUID,
    service: TranscriptionJobService = Depends(get_transcription_job_service),
) -> dict[str, str | int | None]:
    job = _get_completed_job_or_raise(
        job_id=job_id,
        service=service,
    )

    return {
        "job_id": str(job.id),
        "language": job.language,
        "transcription": job.transcription,
        "word_count": len(job.transcription.split()) if job.transcription else 0,
    }


@router.get("/transcribe/{job_id}/txt", response_class=PlainTextResponse)
def get_transcription_txt_output(
    job_id: UUID,
    service: TranscriptionJobService = Depends(get_transcription_job_service),
) -> PlainTextResponse:
    job = _get_completed_job_or_raise(
        job_id=job_id,
        service=service,
    )

    return PlainTextResponse(
        content=job.transcription or "",
        media_type="text/plain; charset=utf-8",
        headers={
            "Content-Disposition": f'inline; filename="{job.id}.txt"',
        },
    )


@router.get("/transcribe/{job_id}/vtt")
def get_transcription_vtt_output(
    job_id: UUID,
    service: TranscriptionJobService = Depends(get_transcription_job_service),
) -> Response:
    job = _get_completed_job_or_raise(
        job_id=job_id,
        service=service,
    )

    return Response(
        content=job.vtt_content or "",
        media_type="text/vtt; charset=utf-8",
        headers={
            "Content-Disposition": f'inline; filename="{job.id}.vtt"',
        },
    )


def _to_status_response(job: TranscriptionJob) -> TranscriptionStatusResponse:
    return TranscriptionStatusResponse(
        job_id=job.id,
        status=job.status,
        progress=job.progress,
        transcription=job.transcription,
        vtt_content=job.vtt_content,
        created_at=job.created_at,
        finished_at=job.finished_at,
        error=job.error,
    )


def _get_completed_job_or_raise(
    *,
    job_id: UUID,
    service: TranscriptionJobService,
) -> TranscriptionJob:
    job = service.get_job(job_id)

    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transcription job not found",
        )

    if job.status is not TranscriptionJobStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Transcription job is not completed yet",
        )

    return job
