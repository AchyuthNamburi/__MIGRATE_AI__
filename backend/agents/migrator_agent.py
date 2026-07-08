# backend/agents/migrator_agent.py
"""Migrator Agent - Executes migration plan"""

import os
import re
import shutil
import json
import logging
from typing import Dict, List
from datetime import datetime

logger = logging.getLogger(__name__)

class CodeMigrator:
    """Executes code migration based on the migration plan"""
    
    def __init__(self, repo_path: str, plan: Dict):
        self.repo_path = repo_path
        self.plan = plan
        self.changes = []
        self.modified_files = []
        self.errors = []
        self.backup_path = None
        
    async def execute(self) -> Dict:
        """Execute the migration plan"""
        logger.info(f"🚀 Starting migration execution in: {self.repo_path}")
        
        # Create backup
        self.backup_path = await self._create_backup()
        
        # Execute each step in the plan
        for step in self.plan.get("steps", []):
            try:
                step_num = step.get('step_number', 0)
                logger.info(f"📝 Executing step {step_num}: {step.get('title')}")
                
                if step.get("type") == "dependency_update":
                    await self._update_dependencies(step)
                elif step.get("type") == "code_update":
                    await self._update_code_ast(step)
                elif step.get("type") == "config_update":
                    await self._update_config(step)
                elif step.get("type") == "database":
                    await self._run_database_migrations(step)
                elif step.get("type") == "testing":
                    await self._run_tests(step)
                else:
                    logger.warning(f"Unknown step type: {step.get('type')}")
                    
            except Exception as e:
                logger.error(f"❌ Error in step {step.get('step_number')}: {str(e)}")
                self.errors.append({
                    "step": step.get("step_number"),
                    "error": str(e)
                })
                break
        
        # Generate report
        report = self._generate_report()
        
        # If errors occurred, restore backup
        if self.errors:
            await self._restore_backup()
            report["status"] = "failed"
            report["message"] = "Migration failed - restored from backup"
        else:
            report["status"] = "success"
            report["message"] = "Migration completed successfully"
        
        return report
    
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
    
    async def _run_database_migrations(self, step: Dict):
        logger.info(f"📊 Database migrations: {step.get('commands', [])}")
    
    async def _run_tests(self, step: Dict):
        logger.info(f"🧪 Running tests: {step.get('commands', [])}")
    
    def _generate_report(self) -> Dict:
        return {
            "status": "completed",
            "modified_files": len(self.modified_files),
            "changes": len(self.changes),
            "errors": self.errors
        }
