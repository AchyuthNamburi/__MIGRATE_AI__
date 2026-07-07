# backend/workers/celery_app.py
from celery import Celery
import os

app = Celery(
    'migration_worker',
    broker=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('REDIS_URL', 'redis://localhost:6379/1')
)

app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_default_queue='migration',
    task_queues={
        'migration': {
            'exchange': 'migration',
            'routing_key': 'migration',
        },
        'high_priority': {
            'exchange': 'high_priority',
            'routing_key': 'high_priority',
        }
    }
)

# backend/workers/tasks.py
from celery import Task
from backend.agents.migration_orchestrator import MigrationOrchestrator
import asyncio

class MigrationTask(Task):
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        # Handle failure
        pass
    
    def on_success(self, retval, task_id, args, kwargs):
        # Handle success
        pass

@app.task(base=MigrationTask, bind=True)
async def run_migration(self, job_id: str):
    """Run migration job"""
    try:
        orchestrator = MigrationOrchestrator()
        result = await orchestrator.run_migration(job_id)
        
        # Update job status
        await update_job_status(job_id, "completed", result)
        
        return result
    except Exception as e:
        # Retry with exponential backoff
        self.retry(exc=e, countdown=60 * (2 ** self.request.retries))