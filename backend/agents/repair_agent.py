# backend/agents/repair_agent.py
"""Repair Agent - Self-heals test failures (max 3 attempts)"""

import os
import json
import re
from typing import Dict, List, Optional
from datetime import datetime

from backend.core.llm import get_llm
from backend.tools.file_tools import FileTools
from backend.tools.command_tools import CommandTools
from backend.agents.memory_system import MemorySystem


class RepairAgent:
    """
    Repair Agent self-heals test failures:
    1. Analyzes test failures using LLM
    2. Suggests and applies fixes
    3. Re-runs tests (max 3 attempts)
    """

    MAX_ATTEMPTS = 3

    def __init__(self, memory: MemorySystem):
        self.memory = memory
        self.llm = get_llm()
        self.file_tools = FileTools()
        self.command_tools = CommandTools()
        self.attempts = 0
        self.repair_history = []

    async def repair(self, repo_path: str, test_result: Dict) -> Dict:
        """
        Repair test failures using LLM (max 3 attempts).
        """
        print(f"🔧 Repair Agent: Attempting to fix test failures")

        if test_result.get('passed', 0) > 0 and test_result.get('failed', 0) == 0:
            print("   ✅ No failures to repair.")
            return {"status": "no_failures", "attempts": 0}

        self.attempts = 0
        self.repair_history = []

        while self.attempts < self.MAX_ATTEMPTS:
            self.attempts += 1
            print(f"\n   🔄 Repair Attempt {self.attempts}/{self.MAX_ATTEMPTS}")

            # 1. Analyze the failure
            failure_analysis = await self._analyze_failure(test_result, repo_path)
            print(f"      📋 Analysis: {failure_analysis.get('summary', 'Unknown issue')[:100]}")

            # 2. Generate fix
            fix = await self._generate_fix(repo_path, failure_analysis)
            if not fix:
                print(f"      ❌ Could not generate fix.")
                continue

            # 3. Apply fix
            applied = await self._apply_fix(repo_path, fix)
            if not applied:
                print(f"      ❌ Could not apply fix.")
                continue

            # 4. Re-run tests
            test_framework = test_result.get('framework', 'django')
            new_test_result = await self._rerun_tests(repo_path, test_framework)

            # 5. Check if fixed
            if new_test_result.get('failed', 0) == 0:
                print(f"      ✅ Fixed! All tests passing.")
                return {
                    "status": "fixed",
                    "attempts": self.attempts,
                    "history": self.repair_history,
                    "final_test_result": new_test_result
                }

            # 6. Update test_result for next iteration
            test_result = new_test_result

        # Max attempts reached
        print(f"\n   ❌ Max attempts ({self.MAX_ATTEMPTS}) reached. Manual review required.")
        return {
            "status": "manual_review",
            "attempts": self.attempts,
            "history": self.repair_history,
            "final_test_result": test_result
        }

    async def _analyze_failure(self, test_result: Dict, repo_path: str) -> Dict:
        """LLM analyzes the test failure and suggests a fix"""
        output = test_result.get('full_output', '')
        framework = test_result.get('framework', 'django')

        prompt = f"""
        You are a test failure analyst. Analyze these test failures and suggest a fix.

        Framework: {framework}
        Test Output:
        {output[:4000]}

        Return JSON with:
        {{
            "issues": [
                {{
                    "type": "error type",
                    "description": "what failed",
                    "root_cause": "why it failed",
                    "suggested_fix": "how to fix it",
                    "file": "path to the file that needs fixing"
                }}
            ],
            "summary": "overall summary of failures",
            "priority": "which issue to fix first"
        }}
        """

        response = self.llm.invoke(prompt)

        try:
            return json.loads(response.content)
        except json.JSONDecodeError:
            match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except:
                    pass

            return {
                "issues": [{
                    "type": "unknown",
                    "description": "Failed to analyze failure",
                    "root_cause": "Unknown",
                    "suggested_fix": "Manual review required",
                    "file": ""
                }],
                "summary": "Failed to analyze failures",
                "priority": "unknown"
            }

    async def _generate_fix(self, repo_path: str, analysis: Dict) -> Optional[Dict]:
        """LLM generates the actual fix code"""
        issues = analysis.get('issues', [])

        for issue in issues:
            suggested_fix = issue.get('suggested_fix', '')
            file_path = issue.get('file', '')

            if suggested_fix and file_path:
                full_path = os.path.join(repo_path, file_path)
                if not os.path.exists(full_path):
                    # Try to find the file
                    found_files = self._find_file(repo_path, file_path)
                    if found_files:
                        full_path = found_files[0]
                    else:
                        continue

                original_content = self.file_tools.read_file(full_path)
                if original_content is None:
                    continue

                prompt = f"""
                You are a code repair expert. Fix this code.

                File: {file_path}
                Issue: {issue.get('description', '')}
                Root Cause: {issue.get('root_cause', '')}
                Suggested Fix: {suggested_fix}

                ORIGINAL CODE:
                {original_content[:3000]}

                Return ONLY the fixed code. No explanations. Just the code.
                """

                response = self.llm.invoke(prompt)
                new_content = response.content

                if new_content and new_content != original_content:
                    self.repair_history.append({
                        "attempt": self.attempts,
                        "file": file_path,
                        "issue": issue.get('description', ''),
                        "fix_applied": True
                    })

                    return {
                        "file": file_path,
                        "original_content": original_content,
                        "new_content": new_content,
                        "full_path": full_path
                    }

        return None

    async def _apply_fix(self, repo_path: str, fix: Dict) -> bool:
        """Apply the fix to the file"""
        try:
            full_path = fix.get('full_path')
            new_content = fix.get('new_content')

            if not full_path or not new_content:
                return False

            success = self.file_tools.write_file(full_path, new_content)

            if success:
                print(f"      ✅ Applied fix to: {os.path.basename(full_path)}")
                return True

            return False

        except Exception as e:
            print(f"      ❌ Error applying fix: {str(e)}")
            return False

    async def _rerun_tests(self, repo_path: str, framework: str) -> Dict:
        """Re-run tests after applying a fix"""
        from backend.agents.verification_agent import VerificationAgent

        # Create a temporary memory for verification
        temp_memory = MemorySystem(f"repair_{datetime.utcnow().timestamp()}")
        temp_memory.set_project_info(self.memory.get_project_info())

        verifier = VerificationAgent(temp_memory)
        result = await verifier._run_tests(repo_path, framework)

        return result

    def _find_file(self, repo_path: str, file_pattern: str) -> List[str]:
        """Find files matching a pattern"""
        matches = []
        for root, dirs, files in os.walk(repo_path):
            if any(skip in root for skip in ['.git', '__pycache__', 'node_modules', 'venv']):
                continue
            for file in files:
                if file_pattern in file or file == file_pattern:
                    matches.append(os.path.join(root, file))
        return matches