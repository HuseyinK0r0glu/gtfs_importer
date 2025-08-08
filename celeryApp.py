from celery import Celery

# RabbitMQ
# amqp ==> advanced message queueing protocol
CELERY_BROKER_URL = "amqp://guest:guest@localhost:5672//" 
CELERY_RESULT_BACKEND = "rpc://"

celery_app = Celery(
    "gtfs_importer",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=["tasks"]   
) 

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)