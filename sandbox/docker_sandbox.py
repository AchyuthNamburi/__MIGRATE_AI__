# backend/sandbox/docker_sandbox.py
"""Docker Sandbox - Run migrations in isolated containers"""

import docker
import os
import shutil
import logging
from typing import Dict, Optional, Any
from datetime import datetime
import tempfile

logger = logging.getLogger(__name__)

class DockerSandbox:
    """Runs migrations in isolated Docker containers"""
    
    def __init__(self):
        self.client = docker.from_env()
        self.container = None
        self.container_name = None
        self.work_dir = "/workspace"
        
    async def create_sandbox(self, repo_path: str, language: str = "python") -> str:
        """
        Create an isolated Docker container
        
        Args:
            repo_path: Path to the repository
            language: Programming language (python, node, java)
        
        Returns:
            Container ID
        """
        try:
            logger.info(f"🐳 Creating Docker sandbox for: {repo_path}")
            
            # Get base image
            image = self._get_base_image(language)
            
            # Generate container name
            self.container_name = f"migration_sandbox_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            # Create container
            self.container = self.client.containers.create(
                image=image,
                name=self.container_name,
                working_dir=self.work_dir,
                detach=True,
                tty=True,
                mem_limit="2g",
                memswap_limit="4g",
                cpu_period=100000,
                cpu_quota=50000,  # 0.5 CPU
                network_disabled=False,  # Allow network for pip install
                volumes={
                    repo_path: {
                        "bind": self.work_dir,
                        "mode": "rw"
                    }
                },
                environment={
                    "PYTHONUNBUFFERED": "1",
                    "PIP_NO_CACHE_DIR": "1"
                }
            )
            
            # Start container
            self.container.start()
            logger.info(f"✅ Container started: {self.container_name}")
            
            return self.container.id
            
        except Exception as e:
            logger.error(f"❌ Failed to create sandbox: {str(e)}")
            raise
    
    async def execute_command(self, command: str, timeout: int = 300) -> Dict:
        """
        Execute a command inside the container
        
        Args:
            command: Command to execute
            timeout: Timeout in seconds
        
        Returns:
            Dict with success, output, error
        """
        if not self.container:
            raise ValueError("No container created. Call create_sandbox first.")
        
        try:
            logger.info(f"📦 Executing in container: {command}")
            
            # Execute command
            exec_result = self.container.exec_run(
                command,
                stream=False,
                demux=True,
                workdir=self.work_dir
            )
            
            # Parse output
            stdout = exec_result.output[0].decode() if exec_result.output[0] else ""
            stderr = exec_result.output[1].decode() if exec_result.output[1] else ""
            
            return {
                "success": exec_result.exit_code == 0,
                "output": stdout + stderr,
                "exit_code": exec_result.exit_code
            }
            
        except Exception as e:
            logger.error(f"❌ Command execution failed: {str(e)}")
            return {
                "success": False,
                "output": str(e),
                "exit_code": -1
            }
    
    async def install_dependencies(self) -> Dict:
        """Install project dependencies"""
        try:
            # Check for requirements.txt
            check_result = await self.execute_command("test -f requirements.txt && echo 'exists' || echo 'not found'")
            
            if "exists" in check_result["output"]:
                logger.info("📦 Installing Python dependencies...")
                return await self.execute_command("pip install -r requirements.txt", timeout=600)
            
            # Check for package.json
            check_result = await self.execute_command("test -f package.json && echo 'exists' || echo 'not found'")
            
            if "exists" in check_result["output"]:
                logger.info("📦 Installing Node dependencies...")
                return await self.execute_command("npm install", timeout=600)
            
            return {"success": True, "output": "No dependencies to install", "exit_code": 0}
            
        except Exception as e:
            logger.error(f"❌ Dependency installation failed: {str(e)}")
            return {"success": False, "output": str(e), "exit_code": -1}
    
    async def run_migration(self, command: str) -> Dict:
        """Run migration command"""
        return await self.execute_command(command, timeout=600)
    
    async def run_tests(self) -> Dict:
        """Run tests inside container"""
        # Check for Django
        check_result = await self.execute_command("test -f manage.py && echo 'django' || echo 'not'")
        
        if "django" in check_result["output"]:
            return await self.execute_command("python manage.py test --noinput", timeout=300)
        
        # Check for pytest
        check_result = await self.execute_command("test -f pytest.ini && echo 'pytest' || echo 'not'")
        
        if "pytest" in check_result["output"]:
            return await self.execute_command("pytest -v", timeout=300)
        
        # Check for npm test
        check_result = await self.execute_command("test -f package.json && echo 'node' || echo 'not'")
        
        if "node" in check_result["output"]:
            return await self.execute_command("npm test", timeout=300)
        
        return {"success": True, "output": "No tests found", "exit_code": 0}
    
    async def cleanup(self):
        """Clean up container"""
        try:
            if self.container:
                logger.info(f"🧹 Cleaning up container: {self.container_name}")
                self.container.stop()
                self.container.remove()
                logger.info("✅ Container removed")
        except Exception as e:
            logger.warning(f"⚠️ Cleanup warning: {str(e)}")
    
    def _get_base_image(self, language: str) -> str:
        """Get base image for language"""
        images = {
            "python": "python:3.11-slim",
            "node": "node:18-alpine",
            "java": "openjdk:11-slim",
            "go": "golang:1.21-alpine",
            "ruby": "ruby:3.2-slim"
        }
        return images.get(language.lower(), "python:3.11-slim")
    
    async def get_container_status(self) -> Dict:
        """Get container status"""
        if not self.container:
            return {"status": "not_created"}
        
        try:
            self.container.reload()
            return {
                "status": self.container.status,
                "name": self.container.name,
                "id": self.container.id,
                "created": self.container.attrs.get("Created")
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}