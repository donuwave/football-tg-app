from app.tasks.celery_app import celery_app


@celery_app.task(name="publisher.publish_batch", queue="publisher")
def publish_batch(batch_id: str) -> dict[str, str]:
    return {
        "status": "queued",
        "batch_id": batch_id,
    }
