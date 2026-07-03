from celery import Celery
from dotenv import load_dotenv
import os

load_dotenv()


celery_app = Celery('smart_audit',
                    broker=os.getenv("RABBITMQ_URL"),
                    include=['celery_worker.tasks'])


celery_app.conf.update(
  task_serializer='json',
  accept_content=['json'],
  task_acks_late=True,
  worker_prefetch_multiplier=1
)