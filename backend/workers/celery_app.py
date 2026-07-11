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

import asyncio
from backend.agents.memory_system import MemorySystem
from backend.agents.discovery_agent import DiscoveryAgent
from backend.agents.planning_agent import PlanningAgent
from backend.agents.migration_agent import CodeMigrator
from backend.agents.verification_agent import VerificationAgent

async def async_run_migration(self, repo_id: str, clone_path: str):
    memory = MemorySystem(repo_id)
    
    self.update_state(state='PROGRESS', meta={'step': 'discovery', 'progress': 20, 'message': 'Analyzing repository...'})
    discovery = DiscoveryAgent(memory)
    analysis = await discovery.discover(clone_path)
    
    self.update_state(state='PROGRESS', meta={'step': 'planning', 'progress': 40, 'message': 'Creating migration plan...', 'framework': analysis.get('framework', 'Unknown')})
    planning = PlanningAgent(memory)
    plan = await planning.plan(analysis)
    
    self.update_state(state='PROGRESS', meta={'step': 'migrating', 'progress': 60, 'message': 'Executing migration...'})
    migrator = CodeMigrator(clone_path, plan)
    migrate_result = await migrator.execute()
    
    self.update_state(state='PROGRESS', meta={'step': 'verifying', 'progress': 80, 'message': 'Verifying migration...'})
    verifier = VerificationAgent(memory)
    verify_result = await verifier.verify(clone_path)
    
    return {
        "status": "success",
        "framework": analysis.get('framework', 'Unknown'),
        "steps_planned": len(plan.get('steps', [])),
        "files_modified": migrate_result.get('modified_files', 0),
        "tests_passed": verify_result.get('passed', 0)
    }

@app.task(bind=True)
def run_migration(self, repo_id: str, clone_path: str):
    """Run migration job fully inside celery"""
    try:
        return asyncio.run(async_run_migration(self, repo_id, clone_path))
    except Exception as e:
        self.update_state(state='FAILURE', meta={'exc_type': type(e).__name__, 'exc_message': str(e)})
        raise e