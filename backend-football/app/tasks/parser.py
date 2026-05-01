from app.tasks.celery_app import celery_app


@celery_app.task(name="parser.sync_source", queue="parser")
def sync_source(source_id: str) -> dict[str, str]:
    return {
        "status": "queued",
        "source_id": source_id,
    }
