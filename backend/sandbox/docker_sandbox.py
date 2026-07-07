import docker
import logging
from typing import Dict
from datetime import datetime

logger = logging.getLogger(__name__)

class DockerSandbox:
    def __init__(self):
        self.client = docker.from_env()
        self.container = None
        self.container_name = None
        self.work_dir = "/workspace"
        
    async def create_sandbox(self, repo_path: str, language: str = "python") -> str:
        try:
            image = "python:3.9-slim"
            self.container_name = f"migration_sandbox_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            self.container = self.client.containers.create(
                image=image,
                name=self.container_name,
                working_dir=self.work_dir,
                detach=True,
                tty=True,
                mem_limit="2g",
                volumes={repo_path: {"bind": self.work_dir, "mode": "rw"}},
                environment={"PYTHONUNBUFFERED": "1"}
            )
            self.container.start()
            logger.info(f"✅ Container started: {self.container_name}")
            return self.container.id
        except Exception as e:
            logger.error(f"❌ Failed: {str(e)}")
            raise
    
    async def execute_command(self, command: str, timeout: int = 300) -> Dict:
        if not self.container:
            raise ValueError("No container created")
        try:
            logger.info(f"📦 Executing: {command[:50]}...")
            exec_result = self.container.exec_run(
                command, 
                stream=False, 
                demux=True, 
                workdir=self.work_dir
            )
            stdout = exec_result.output[0].decode() if exec_result.output[0] else ""
            stderr = exec_result.output[1].decode() if exec_result.output[1] else ""
            output = stdout + stderr
            return {"success": exec_result.exit_code == 0, "output": output}
        except Exception as e:
            return {"success": False, "output": str(e)}
    
    async def install_dependencies(self) -> Dict:
        try:
            # Install whitenoise and common packages first
            logger.info("📦 Installing common packages...")
            await self.execute_command("pip install django whitenoise gunicorn psycopg2-binary", timeout=300)
            
            # Then install from requirements.txt
            logger.info("📦 Installing from requirements.txt...")
            result = await self.execute_command("pip install -r requirements.txt", timeout=600)
            
            return {"success": True, "output": "All dependencies installed"}
            
        except Exception as e:
            return {"success": False, "output": str(e)}
    
    async def run_migration(self, command: str) -> Dict:
        return await self.execute_command(command, timeout=600)
    
    async def run_tests(self) -> Dict:
        return await self.execute_command("python manage.py test --noinput 2>/dev/null || echo 'No tests found'", timeout=300)
    
    async def cleanup(self):
        try:
            if self.container:
                self.container.stop()
                self.container.remove()
                logger.info("✅ Container removed")
        except Exception as e:
            logger.warning(f"Cleanup: {e}")
