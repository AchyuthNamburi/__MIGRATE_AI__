# backend/docker_runner/docker_manager.py
import docker
from docker.models.containers import Container
import asyncio
import tempfile
import shutil

class DockerManager:
    def __init__(self):
        self.client = docker.from_env()
        self.containers = {}
    
    async def create_sandbox(self, repo_path: str, language: str) -> str:
        """Create isolated Docker container for migration"""
        
        # Select base image
        base_image = self.get_base_image(language)
        
        # Create container
        container = self.client.containers.create(
            image=base_image,
            detach=True,
            tty=True,
            working_dir="/workspace",
            mem_limit="2g",
            cpu_period=100000,
            cpu_quota=50000,  # 0.5 CPU
            network_disabled=True,
            volumes={
                repo_path: {
                    "bind": "/workspace",
                    "mode": "rw"
                }
            }
        )
        
        container.start()
        self.containers[container.id] = container
        return container.id
    
    async def execute_command(self, container_id: str, command: str) -> Dict:
        """Execute command in container"""
        container = self.containers.get(container_id)
        if not container:
            raise ValueError("Container not found")
        
        # Execute with timeout
        try:
            result = await asyncio.wait_for(
                self._run_command(container, command),
                timeout=300  # 5 minutes timeout
            )
            return {
                "success": result.exit_code == 0,
                "stdout": result.output.decode(),
                "stderr": result.error.decode(),
                "exit_code": result.exit_code
            }
        except asyncio.TimeoutError:
            return {
                "success": False,
                "error": "Command timed out after 5 minutes"
            }
    
    async def _run_command(self, container: Container, command: str):
        """Run command and return result"""
        exec_result = container.exec_run(
            command,
            stream=True,
            demux=True
        )
        return exec_result
    
    async def cleanup(self, container_id: str):
        """Clean up container and resources"""
        if container_id in self.containers:
            container = self.containers[container_id]
            container.stop()
            container.remove()
            del self.containers[container_id]
    
    def get_base_image(self, language: str) -> str:
        """Get appropriate base image for language"""
        images = {
            'python': 'python:3.11-slim',
            'node': 'node:18-alpine',
            'java': 'openjdk:11-slim',
            'golang': 'golang:1.21-alpine'
        }
        return images.get(language, 'alpine:latest')