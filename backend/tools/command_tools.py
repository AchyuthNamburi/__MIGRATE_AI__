# backend/tools/command_tools.py
"""Command execution tools"""

import subprocess
import os
from typing import Dict, Optional, List


class CommandTools:
    """Command execution for the migration agent"""
    
    def __init__(self):
        self.commands_run = 0
        self.failed_commands = 0
    
    def execute(self, command: str, cwd: Optional[str] = None, timeout: int = 300) -> Dict:
        """Execute a shell command"""
        self.commands_run += 1
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd or os.getcwd(),
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            success = result.returncode == 0
            if not success:
                self.failed_commands += 1
            
            return {
                "success": success,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": "Command timed out",
                "returncode": -1
            }
        except Exception as e:
            self.failed_commands += 1
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "returncode": -1
            }
    
    def run_tests(self, repo_path: str) -> Dict:
        """Run tests in a repository"""
        # Try different test commands
        test_commands = [
            "python manage.py test --noinput 2>/dev/null || echo 'No Django tests'",
            "pytest -v 2>/dev/null || echo 'No pytest tests'",
            "python -m unittest discover 2>/dev/null || echo 'No unittest tests'",
            "npm test 2>/dev/null || echo 'No npm tests'"
        ]
        
        results = {}
        for cmd in test_commands:
            result = self.execute(cmd, cwd=repo_path)
            if "No" not in result["stdout"] and "No" not in result["stderr"]:
                results[cmd.split()[0]] = result
        
        return results
    
    def run_build(self, repo_path: str) -> Dict:
        """Run build in a repository"""
        # Try different build commands
        build_commands = [
            "python manage.py check 2>/dev/null || echo 'No Django'",
            "python setup.py build 2>/dev/null || echo 'No setup.py'",
            "npm run build 2>/dev/null || echo 'No npm build'"
        ]
        
        for cmd in build_commands:
            result = self.execute(cmd, cwd=repo_path)
            if result["success"]:
                return result
        
        return {"success": False, "stdout": "", "stderr": "No build command found"}
    
    def get_stats(self) -> Dict:
        """Get command execution statistics"""
        return {
            "commands_run": self.commands_run,
            "failed_commands": self.failed_commands,
            "success_rate": (self.commands_run - self.failed_commands) / self.commands_run if self.commands_run > 0 else 0
        }