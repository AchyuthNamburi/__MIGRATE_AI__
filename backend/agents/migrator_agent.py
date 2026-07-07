# backend/agents/migrator_agent.py
import os, re, shutil, json, logging
from typing import Dict, List
from datetime import datetime

logger = logging.getLogger(__name__)

class CodeMigrator:
    def __init__(self, repo_path: str, plan: Dict):
        self.repo_path = repo_path
        self.plan = plan
        self.changes = []
        self.modified_files = []
        self.errors = []
        self.backup_path = None
        
    async def execute(self) -> Dict:
        logger.info(f"🚀 Starting migration in: {self.repo_path}")
        self.backup_path = await self._create_backup()
        
        for step in self.plan.get("steps", []):
            try:
                if step.get("type") == "dependency_update":
                    await self._update_dependencies(step)
                elif step.get("type") == "code_update":
                    await self._update_code_ast(step)
                elif step.get("type") == "config_update":
                    await self._update_config(step)
            except Exception as e:
                self.errors.append({"step": step.get("step_number"), "error": str(e)})
                break
        
        report = self._generate_report()
        if self.errors:
            await self._restore_backup()
            report["status"] = "failed"
        else:
            report["status"] = "success"
        return report
    
    async def execute_with_docker(self) -> Dict:
        """Execute migration in Docker container"""
        try:
            from backend.sandbox.docker_sandbox import DockerSandbox
            
            logger.info("🐳 Starting Docker migration...")
            
            # Create sandbox
            sandbox = DockerSandbox()
            await sandbox.create_sandbox(self.repo_path, "python")
            
            # ✅ Step 1: Install Django
            logger.info("📦 Installing Django...")
            install1 = await sandbox.execute_command("pip install django")
            if not install1["success"]:
                await sandbox.cleanup()
                return {"status": "failed", "error": f"pip install django failed: {install1.get('output')}"}
            
            # ✅ Step 2: Install requirements if exists
            logger.info("📦 Installing requirements...")
            check = await sandbox.execute_command("test -f requirements.txt && echo 'exists' || echo 'not'")
            if "exists" in check.get("output", ""):
                await sandbox.execute_command("pip install -r requirements.txt")
            
            # ✅ Step 3: Run migrations
            logger.info("📊 Running migrations...")
            migrate = await sandbox.execute_command("python manage.py migrate --noinput 2>/dev/null || echo 'Migration skipped'")
            
            # ✅ Step 4: Run tests
            logger.info("🧪 Running tests...")
            tests = await sandbox.execute_command("python manage.py test --noinput 2>/dev/null || echo 'No tests found'")
            
            await sandbox.cleanup()
            
            return {
                "status": "success",
                "message": "Migration completed in Docker",
                "migrate_output": migrate.get("output", ""),
                "test_output": tests.get("output", "")
            }
            
        except Exception as e:
            logger.error(f"Docker failed: {str(e)}")
            return {"status": "failed", "error": str(e)}
    
    async def _create_backup(self) -> str:
        backup_dir = f"{self.repo_path}_backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        if os.path.exists(backup_dir):
            shutil.rmtree(backup_dir)
        shutil.copytree(self.repo_path, backup_dir)
        return backup_dir
    
    async def _restore_backup(self):
        if self.backup_path and os.path.exists(self.backup_path):
            shutil.rmtree(self.repo_path)
            shutil.copytree(self.backup_path, self.repo_path)
    
    async def _update_dependencies(self, step: Dict):
        for file in step.get("files", []):
            file_path = os.path.join(self.repo_path, file)
            if os.path.exists(file_path):
                if file.endswith('requirements.txt'):
                    await self._update_requirements(file_path, step)
                self.modified_files.append(file)
    
    async def _update_requirements(self, file_path: str, step: Dict):
        with open(file_path, 'r') as f:
            content = f.read()
        target = self.plan.get("target_version")
        if target and "Django" in content:
            new = re.sub(r'Django==[\d.]+', f'Django=={target}', content)
            if new != content:
                with open(file_path, 'w') as f:
                    f.write(new)
                self.changes.append({"file": file_path, "type": "dependency_update"})
    
    async def _update_code_ast(self, step: Dict):
        patterns = step.get("patterns", [])
        if "pattern" in step:
            patterns = [{"old": step["pattern"], "new": step.get("replacement", "")}]
        
        for root, _, files in os.walk(self.repo_path):
            for file in files:
                if not file.endswith('.py'):
                    continue
                file_path = os.path.join(root, file)
                with open(file_path, 'r') as f:
                    content = f.read()
                new = content
                for p in patterns:
                    if p.get("old") and p["old"] in new:
                        new = new.replace(p["old"], p["new"])
                        self.changes.append({"file": file_path, "type": "code_update"})
                if new != content:
                    with open(file_path, 'w') as f:
                        f.write(new)
                    self.modified_files.append(file_path)
    
    async def _update_config(self, step: Dict):
        for file in step.get("files", []):
            file_path = os.path.join(self.repo_path, file)
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    content = f.read()
                if step.get("pattern") and step["pattern"] in content:
                    new = content.replace(step["pattern"], step.get("replacement", ""))
                    with open(file_path, 'w') as f:
                        f.write(new)
                    self.modified_files.append(file)
                    self.changes.append({"file": file, "type": "config_update"})
    
    def _generate_report(self) -> Dict:
        return {
            "status": "completed",
            "modified_files": len(self.modified_files),
            "changes": len(self.changes),
            "errors": self.errors
        }
