from app.core.config import settings
from app.workers.celery_app import celery_app


def test_celery_app_uses_configured_broker() -> None:
    assert celery_app.conf.broker_url == settings.celery_broker_url
    assert celery_app.conf.task_ignore_result is True
    assert "json" in celery_app.conf.accept_content
