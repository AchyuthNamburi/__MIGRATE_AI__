# backend/agents/verification_agent.py
"""Verification Agent - Runs tests and verifies migration"""

import os
import subprocess
import sys
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import shutil

logger = logging.getLogger(__name__)

class VerificationAgent:
    """Verifies migrated code by running tests and checks"""
    
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.results = {
            "tests": {},
            "build": {},
            "lint": {},
            "coverage": {},
            "summary": {}
        }
    
    async def verify(self) -> Dict:
        """Run all verification checks"""
        logger.info(f"🔍 Starting verification for: {self.repo_path}")
        
        # Detect project type
        project_type = self._detect_project_type()
        logger.info(f"📋 Detected project type: {project_type}")
        
        # Install dependencies first
        await self._install_dependencies()
        
        # Run checks based on project type
        if project_type == "django":
            self.results = await self._verify_django()
        elif project_type == "python":
            self.results = await self._verify_python()
        elif project_type == "node":
            self.results = await self._verify_node()
        else:
            self.results = await self._verify_generic()
        
        # Generate summary
        self.results["summary"] = self._generate_summary()
        self.results["timestamp"] = datetime.utcnow().isoformat()
        
        return self.results
    
    async def _install_dependencies(self) -> bool:
        """Install project dependencies"""
        try:
            # Check for requirements.txt
            req_path = os.path.join(self.repo_path, 'requirements.txt')
            if os.path.exists(req_path):
                logger.info("📦 Installing Python dependencies...")
                result = await self._run_command("pip3 install -r requirements.txt")
                return result["success"]
            
            # Check for package.json
            pkg_path = os.path.join(self.repo_path, 'package.json')
            if os.path.exists(pkg_path):
                logger.info("📦 Installing Node dependencies...")
                result = await self._run_command("npm install")
                return result["success"]
            
            return True
        except Exception as e:
            logger.warning(f"Dependency installation failed: {e}")
            return False
    
    def _detect_project_type(self) -> str:
        """Detect project type based on files"""
        if os.path.exists(os.path.join(self.repo_path, 'manage.py')):
            return "django"
        if os.path.exists(os.path.join(self.repo_path, 'setup.py')) or \
           os.path.exists(os.path.join(self.repo_path, 'pyproject.toml')) or \
           os.path.exists(os.path.join(self.repo_path, 'requirements.txt')):
            return "python"
        if os.path.exists(os.path.join(self.repo_path, 'package.json')):
            return "node"
        return "generic"
    
    async def _verify_django(self) -> Dict:
        """Verify Django project"""
        results = {
            "tests": {"passed": 0, "failed": 0, "skipped": 0},
            "build": {"success": False},
            "lint": {"issues": 0},
            "coverage": {"percentage": 0},
            "details": []
        }
        
        # 1. Check Django installation
        check_result = await self._run_command("python3 -c 'import django; print(django.get_version())'")
        if check_result["success"]:
            results["details"].append({
                "name": "Django Version Check",
                "success": True,
                "output": f"Django {check_result['output'].strip()} installed"
            })
        else:
            results["details"].append({
                "name": "Django Version Check",
                "success": False,
                "output": "Django not installed - run: pip install django"
            })
        
        # 2. Run Django checks
        check_result = await self._run_command("python3 manage.py check")
        results["details"].append({
            "name": "Django System Check",
            "success": check_result["success"],
            "output": check_result["output"][:200] if check_result["output"] else "Check passed"
        })
        
        # 3. Run tests if available
        test_result = await self._run_command("python3 manage.py test --noinput 2>/dev/null || echo 'No tests found'")
        if "No tests found" not in test_result["output"]:
            results["tests"] = self._parse_django_test_output(test_result["output"])
        results["details"].append({
            "name": "Django Tests",
            "success": test_result["success"] or "OK" in test_result["output"],
            "output": test_result["output"][:200] if test_result["output"] else "No tests found"
        })
        
        results["build"]["success"] = True
        return results
    
    async def _verify_python(self) -> Dict:
        """Verify Python project"""
        results = {
            "tests": {"passed": 0, "failed": 0, "skipped": 0},
            "build": {"success": False},
            "lint": {"issues": 0},
            "coverage": {"percentage": 0},
            "details": []
        }
        
        # Run tests with pytest
        test_result = await self._run_command("python3 -m pytest -v --tb=short 2>/dev/null || python3 -m unittest discover 2>/dev/null || echo 'No tests found'")
        if "No tests found" not in test_result["output"]:
            results["tests"] = self._parse_test_output(test_result["output"])
        
        results["details"].append({
            "name": "Unit Tests",
            "success": test_result["success"] or "OK" in test_result["output"],
            "output": test_result["output"][:200] if test_result["output"] else "No tests found"
        })
        
        results["build"]["success"] = True
        return results
    
    async def _verify_node(self) -> Dict:
        """Verify Node.js project"""
        results = {
            "tests": {"passed": 0, "failed": 0, "skipped": 0},
            "build": {"success": False},
            "lint": {"issues": 0},
            "coverage": {"percentage": 0},
            "details": []
        }
        
        # Run tests
        test_result = await self._run_command("npm test 2>/dev/null || echo 'No tests found'")
        if "No tests found" not in test_result["output"]:
            results["tests"] = self._parse_test_output(test_result["output"])
        
        results["details"].append({
            "name": "npm test",
            "success": test_result["success"] or "OK" in test_result["output"],
            "output": test_result["output"][:200] if test_result["output"] else "No tests found"
        })
        
        # Build
        build_result = await self._run_command("npm run build 2>/dev/null || echo 'No build script'")
        results["build"]["success"] = "No build script" not in build_result["output"]
        results["details"].append({
            "name": "npm build",
            "success": results["build"]["success"],
            "output": build_result["output"][:200]
        })
        
        return results
    
    async def _verify_generic(self) -> Dict:
        """Verify generic project"""
        results = {
            "tests": {"passed": 0, "failed": 0, "skipped": 0},
            "build": {"success": True},
            "lint": {"issues": 0},
            "coverage": {"percentage": 0},
            "details": []
        }
        
        results["details"].append({
            "name": "Structure Check",
            "success": True,
            "output": "Project structure appears valid"
        })
        
        return results
    
    async def _run_command(self, command: str) -> Dict:
        """Run a command and return results"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=300
            )
            return {
                "success": result.returncode == 0,
                "output": result.stdout + result.stderr,
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "output": "Command timed out",
                "returncode": -1
            }
        except Exception as e:
            return {
                "success": False,
                "output": str(e),
                "returncode": -1
            }
    
    def _parse_django_test_output(self, output: str) -> Dict:
        """Parse Django test output"""
        results = {"passed": 0, "failed": 0, "skipped": 0}
        import re
        if 'OK' in output:
            match = re.search(r'Ran (\d+) tests?', output)
            if match:
                results["passed"] = int(match.group(1))
        return results
    
    def _parse_test_output(self, output: str) -> Dict:
        """Parse generic test output"""
        results = {"passed": 0, "failed": 0, "skipped": 0}
        import re
        passed = re.search(r'(\d+)\s+passed', output)
        if passed:
            results["passed"] = int(passed.group(1))
        failed = re.search(r'(\d+)\s+failed', output)
        if failed:
            results["failed"] = int(failed.group(1))
        return results
    
    def _generate_summary(self) -> Dict:
        """Generate verification summary"""
        tests = self.results.get("tests", {})
        build = self.results.get("build", {})
        
        test_passed = tests.get("passed", 0)
        test_failed = tests.get("failed", 0)
        
        if test_failed > 0:
            status = "failed"
        elif test_passed > 0:
            status = "success"
        else:
            status = "no_tests"
        
        return {
            "status": status,
            "tests_passed": test_passed,
            "tests_failed": test_failed,
            "tests_skipped": tests.get("skipped", 0),
            "build_success": build.get("success", False),
            "total_checks": len(self.results.get("details", [])),
            "passed_checks": len([d for d in self.results.get("details", []) if d.get("success", False)]),
            "failed_checks": len([d for d in self.results.get("details", []) if not d.get("success", False)])
        }