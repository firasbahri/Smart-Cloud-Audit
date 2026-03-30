from celery import Celery

celery_app = Celery('smart_audit',
                    broker="amqp://guest:guest@localhost:5672//",
                    include=['celery.tasks'])


celery_app.conf.update(
  task_serializer='json',
  accept_content=['json'],
  task_acks_late=True,
  worker_prefetch_multiplier=1
)