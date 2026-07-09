# Whisper Transcription API

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-API-009688?logo=fastapi)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-4169e1?logo=postgresql)
![Redis](https://img.shields.io/badge/Redis-Queue-dc382d?logo=redis)
![Celery](https://img.shields.io/badge/Celery-Worker-37814a)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ed?logo=docker)
![Whisper](https://img.shields.io/badge/OpenAI_Whisper-small-black)

## Table of Contents

* [Description](#description)
* [Features](#features)
* [Tech Stack](#tech-stack)
* [How It Works](#how-it-works)
* [API Endpoints](#api-endpoints)
* [Running the Project with Docker](#running-the-project-with-docker)
* [Manual Testing](#manual-testing)
* [Running Automated Tests](#running-automated-tests)
* [Metrics Logging](#metrics-logging)
* [Project Structure](#project-structure)
* [Notes and Assumptions](#notes-and-assumptions)
* [Possible Improvements](#possible-improvements)
* [Summary](#summary)

## Description

Whisper Transcription API is a backend service for asynchronous speech-to-text transcription of MP3 audio files.

The application exposes REST API endpoints for creating transcription jobs, checking their status, and retrieving completed transcription results in different formats. Audio files are processed in the background by a Celery worker. The transcription is generated with OpenAI Whisper Small, while job data and results are stored in PostgreSQL.

The project demonstrates a backend architecture based on:

* FastAPI for REST API.
* PostgreSQL for persistent job storage.
* Redis and Celery for asynchronous background processing.
* OpenAI Whisper for audio transcription.
* Docker Compose for local development and testing.

The default transcription language is Polish (`pl`), but other languages supported by Whisper can also be used by passing the appropriate language code, for example `en` for English.

## Features

* Create transcription jobs from MP3 audio URLs.
* Return a job identifier immediately after job creation.
* Process transcription asynchronously in the background.
* Track job status and progress.
* Store transcription results in PostgreSQL.
* Generate WebVTT subtitle content.
* Retrieve completed transcription as:

  * JSON
  * TXT
  * WebVTT
* Support multiple languages available in Whisper.
* Send optional webhook callback after job completion or failure.
* Log transcription metrics to a JSON Lines log file.
* Run the whole application locally with Docker Compose.
* Access interactive API documentation through Swagger UI.
* Run unit and integration tests with Pytest.

## Tech Stack

**Backend:** Python 3.11, FastAPI

**Database:** PostgreSQL, SQLAlchemy, Alembic

**Queue:** Redis, Celery

**Speech-to-text:** OpenAI Whisper Small

**HTTP client:** HTTPX

**Containerization:** Docker, Docker Compose

**Testing and tooling:** Pytest, Ruff, uv

## How It Works

The main application flow:

```text
POST /api/v1/transcribe
        ↓
Create transcription job in PostgreSQL
        ↓
Queue background task in Redis
        ↓
Celery worker downloads the MP3 file
        ↓
Worker transcribes audio with Whisper Small
        ↓
Worker generates WebVTT subtitles
        ↓
Worker saves transcription result in PostgreSQL
        ↓
Worker writes metrics log
        ↓
Worker sends webhook callback if webhook_url was provided
```

The application is divided into separate layers:

```text
api/
→ FastAPI routes, request schemas, response schemas, dependencies

domain/
→ Transcription job entity, statuses, progress and state transitions

database/
→ SQLAlchemy models, database session and repositories

services/
→ Application logic, job service, metrics logging, WebVTT generation

integrations/
→ Audio downloader, Whisper transcriber, webhook client

workers/
→ Celery configuration and background transcription tasks
```

This structure keeps API handling, business logic, database access, and external integrations separated.

## API Endpoints
All endpoint paths are relative to the API base URL.

### Health check

```http
GET /api/v1/health
```

Example response:

```json
{
  "status": "ok"
}
```

### Create transcription job

```http
POST /api/v1/transcribe
```

Request body:

```json
{
  "audio_url": "https://example.com/audio.mp3",
  "language": "en",
  "webhook_url": "https://example.com/webhook"
}
```

Fields:

```text
audio_url    required   URL to an MP3 audio file
language     optional   transcription language, default: "pl"
webhook_url  optional   URL called after job completion or failure
```

Example response:

```json
{
  "job_id": "uuid-here",
  "status": "queued",
  "message": "Transcription job created successfully"
}
```

### Get transcription job status

```http
GET /api/v1/transcribe/{job_id}
```

Example response for queued job:

```json
{
  "job_id": "uuid-here",
  "status": "queued",
  "progress": 0,
  "created_at": "2026-07-08T10:30:00+00:00"
}
```

Example response while processing:

```json
{
  "job_id": "uuid-here",
  "status": "processing",
  "progress": 45,
  "created_at": "2026-07-08T10:30:00+00:00"
}
```

Example completed response:

```json
{
  "job_id": "uuid-here",
  "status": "completed",
  "progress": 100,
  "transcription": "Full transcription text...",
  "vtt_content": "WEBVTT\n\n00:00:00.000 --> 00:00:03.000\nFull transcription text...",
  "created_at": "2026-07-08T10:30:00+00:00",
  "completed_at": "2026-07-08T10:32:15+00:00"
}
```

Example failed response:

```json
{
  "job_id": "uuid-here",
  "status": "failed",
  "progress": 30,
  "created_at": "2026-07-08T10:30:00+00:00",
  "completed_at": "2026-07-08T10:31:00+00:00",
  "error": "Failed to download audio file: ..."
}
```

### Get JSON output

```http
GET /api/v1/transcribe/{job_id}/json
```

Example response:

```json
{
  "job_id": "uuid-here",
  "language": "en",
  "transcription": "Good morning. This is a transcription test.",
  "word_count": 8
}
```

### Get TXT output

```http
GET /api/v1/transcribe/{job_id}/txt
```

Example response:

```text
Good morning. This is a transcription test.
```

### Get WebVTT output

```http
GET /api/v1/transcribe/{job_id}/vtt
```

Example response:

```text
WEBVTT

00:00:00.000 --> 00:00:03.000
Good morning. This is a transcription test.
```

### Output endpoint behavior

If the job does not exist:

```http
404 Not Found
```

If the job exists but is not completed yet:

```http
409 Conflict
```

## Running the Project with Docker

The recommended way to run the project is with Docker Compose.

Docker Compose starts all required services:

* FastAPI API container
* PostgreSQL database
* Redis broker
* Celery worker
* database migration service
* local sample audio server
* local webhook receiver

### Prerequisites

Make sure the following tools are installed:

* Git
* Docker
* Docker Compose

### 1. Clone the repository

```bash
git clone https://github.com/szewczem/whisper-transcription-api
cd whisper-transcription-api
```

Replace the repository URL with the actual project URL.

### 2. Create `.env` file

Copy the example environment file:

```bash
cp .env.example .env
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Example `.env` file:

```env
POSTGRES_DB=whisper_transcription
POSTGRES_USER=whisper_app
POSTGRES_PASSWORD=local_dev_password

DATABASE_URL=postgresql+psycopg://whisper_app:local_dev_password@localhost:5432/whisper_transcription
CELERY_BROKER_URL=redis://localhost:6379/0

WHISPER_MODEL_NAME=small
```

For local Python commands, `DATABASE_URL` and `CELERY_BROKER_URL` use `localhost`.

Inside Docker Compose, these values are overridden so containers can communicate using Docker service names such as `postgres` and `redis`.

### 3. Build and start the application

```bash
docker compose up --build
```

Or start it in detached mode:

```bash
docker compose up --build -d
```

The first startup may take longer because Docker needs to build the image and Whisper may need to download the model.

### 4. Check running containers

```bash
docker compose ps
```

You should see services similar to:

```text
postgres
redis
migrate
api
worker
sample-audio-server
webhook-receiver
```

The `migrate` service should finish successfully. The `api`, `worker`, `postgres`, `redis`, `sample-audio-server`, and `webhook-receiver` services should keep running.

### 5. Open the API from your browser

The FastAPI application runs inside Docker, but Docker Compose exposes it on your local machine through port `8000`.

After the containers are running, the API is available at:

```text
http://localhost:8000
```

Interactive Swagger UI documentation is available at:

```text
http://localhost:8000/docs
```

This address is opened from the browser on your computer. Docker forwards the request to the API container.

### 6. Stop the application

```bash
docker compose down
```

To stop the application and remove the PostgreSQL volume:

```bash
docker compose down -v
```

Removing the volume deletes locally stored transcription jobs.

## Manual Testing

Manual testing can be done with any MP3 file available through a URL.

There are two simple options:

```text
1. Use your own public MP3 URL.
2. Use a local MP3 file through sample-audio-server.
```

### Option 1: Test with a local MP3 file

Place an MP3 file in:

```text
data/input/
```

Example:

```text
data/input/test.mp3
```

The `sample-audio-server` service exposes files from this folder.

From your browser or host machine, the file is available at:

```text
http://localhost:9000/test.mp3
```

Inside Docker Compose, the worker can access the same file using:

```text
http://sample-audio-server:9000/test.mp3
```

When creating a transcription job, use the Docker Compose URL:

```text
http://sample-audio-server:9000/test.mp3
```

The worker downloads the file from inside the Docker network, so it needs the Docker service URL, not the browser URL.

### Create a transcription job

Example for Polish audio:

```powershell
$response = Invoke-RestMethod `
  -Method Post `
  -Uri http://localhost:8000/api/v1/transcribe `
  -ContentType "application/json" `
  -Body '{"audio_url":"http://sample-audio-server:9000/test.mp3","language":"pl","webhook_url":"http://webhook-receiver:9001/webhook"}'

$response
```

Example for English audio:

```powershell
$response = Invoke-RestMethod `
  -Method Post `
  -Uri http://localhost:8000/api/v1/transcribe `
  -ContentType "application/json" `
  -Body '{"audio_url":"http://sample-audio-server:9000/test_eng.mp3","language":"en","webhook_url":"http://webhook-receiver:9001/webhook"}'

$response
```

Save the returned job ID:

```powershell
$jobId = $response.job_id
$jobId
```

### Check job status

```powershell
Invoke-RestMethod "http://localhost:8000/api/v1/transcribe/$jobId"
```

Repeat this command until the job status becomes:

```text
completed
```

or:

```text
failed
```

### Get JSON output

```powershell
Invoke-RestMethod "http://localhost:8000/api/v1/transcribe/$jobId/json"
```

### Get TXT output

```powershell
Invoke-WebRequest "http://localhost:8000/api/v1/transcribe/$jobId/txt"
```

### Get WebVTT output

```powershell
Invoke-WebRequest "http://localhost:8000/api/v1/transcribe/$jobId/vtt"
```

### Check worker logs

```bash
docker compose logs worker
```

This is useful for checking whether the worker received and processed the job.

### Check webhook callback

If `webhook_url` was provided, check the webhook receiver logs:

```bash
docker compose logs webhook-receiver
```

Expected log output:

```text
Webhook received: {...}
```

### Check metrics log

After a job is completed or failed, metrics are written to:

```text
logs/transcription_metrics.log
```

On Windows PowerShell:

```powershell
Get-Content logs/transcription_metrics.log
```

On Linux/macOS:

```bash
cat logs/transcription_metrics.log
```

## Running Automated Tests

The project includes unit and integration tests.

### Unit tests

Unit tests do not require Docker services:

```bash
uv run pytest tests/unit
```

### Full test suite

The full test suite includes integration tests that require PostgreSQL and Redis.

Start the required services:

```bash
docker compose up -d postgres redis
```

Run all tests:

```bash
uv run pytest
```

Run only integration tests:

```bash
uv run pytest tests/integration
```

Run code formatting:

```bash
uv run ruff format .
```

Run linting:

```bash
uv run ruff check .
```

If the whole Docker Compose application is already running, the tests can also be executed with:

```bash
uv run pytest
```

## Metrics Logging

The worker writes one JSON object per line to:

```text
logs/transcription_metrics.log
```

Metrics are written after each completed or failed transcription job.

Example log entry:

```json
{"job_id":"uuid-here","timestamp":"2026-07-08T10:32:15.123456+00:00","processing_time":135.42,"audio_url":"http://sample-audio-server:9000/test.mp3","language":"en","word_count":120,"status":"completed","error":null}
```

Logged fields:

```text
job_id            transcription job identifier
timestamp         UTC timestamp
processing_time   processing time in seconds
audio_url         original audio URL
language          transcription language code
word_count        number of words in transcription
status            completed or failed
error             error message if processing failed
```

## Project Structure

```text
whisper-transcription-api/
├── alembic/
│   └── versions/
│
├── app/
│   ├── api/
│   │   ├── dependencies.py
│   │   └── v1/
│   │       ├── health.py
│   │       ├── transcriptions.py
│   │       └── schemas/
│   │           └── transcription.py
│   │
│   ├── core/
│   │   └── config.py
│   │
│   ├── database/
│   │   ├── session.py
│   │   ├── models/
│   │   │   └── transcription_job.py
│   │   └── repositories/
│   │       └── transcription_job_repository.py
│   │
│   ├── domain/
│   │   └── transcription/
│   │       ├── job.py
│   │       └── models.py
│   │
│   ├── integrations/
│   │   ├── audio/
│   │   │   └── audio_downloader.py
│   │   ├── webhook/
│   │   │   └── client.py
│   │   └── whisper/
│   │       └── transcriber.py
│   │
│   ├── services/
│   │   └── transcription/
│   │       ├── job_service.py
│   │       ├── metrics_logger.py
│   │       └── vtt_generator.py
│   │
│   ├── workers/
│   │   ├── celery_app.py
│   │   └── transcription_tasks.py
│   │
│   └── main.py
│
├── data/
│   ├── input/
│   │   └── .gitkeep
│   ├── models/
│   │   └── .gitkeep
│   └── output/
│       └── .gitkeep
│
├── logs/
│   └── .gitkeep
│
├── scripts/
│   ├── check_database.py
│   ├── transcribe_local.py
│   └── webhook_receiver.py
│
├── tests/
│   ├── unit/
│   └── integration/
│
├── Dockerfile
├── compose.yaml
├── pyproject.toml
├── alembic.ini
├── .env.example
└── README.md
```

## Notes and Assumptions

* The API accepts an audio URL, not a direct file upload.
* MP3 is the expected input format.
* The default language is Polish (`pl`).
* Other Whisper-supported languages can be used by passing the appropriate language code, for example `en`.
* Timestamps are returned in UTC.
* The first transcription may take longer because the Whisper model may need to be downloaded.
* Webhook delivery is optional.
* Webhook failure does not change a completed transcription job into a failed job.
* Metrics are written after completed or failed jobs.
* Progress values represent processing stages, not exact audio-duration percentage.

### Progress values

```text
0     queued
10    processing started
30    audio downloaded
45    transcription started
75    transcription completed
85    WebVTT generated
100   completed
```

## Possible Improvements

Possible future improvements include:

* Direct file upload endpoint.
* More detailed validation of audio files.
* Better error messages for failed jobs.
* Job listing endpoint.
* Basic authentication.
* Retry logic for temporary download or webhook errors.
* More detailed tests for full processing flow.
* Support for additional output formats.

## Summary

Whisper Transcription API is a backend service for asynchronous MP3 transcription.

It provides:

* FastAPI REST endpoints.
* PostgreSQL job storage.
* Redis and Celery background processing.
* OpenAI Whisper Small integration.
* WebVTT subtitle generation.
* Optional webhook callback.
* Metrics logging.
* Docker Compose setup for local development and testing.

The project focuses on backend architecture, asynchronous processing, external service integration, and practical API design.