from app.tasks.celery_app import celery_app


@celery_app.task(name="ai.generate_news_post", queue="ai")
def generate_news_post(content_item_id: str) -> dict[str, str]:
    return {
        "status": "queued",
        "content_item_id": content_item_id,
    }
