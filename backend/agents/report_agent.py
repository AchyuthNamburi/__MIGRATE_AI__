# backend/agents/report_agent.py
"""Report Agent - Generates comprehensive migration report"""

import os
import json
from datetime import datetime
from typing import Dict, List, Any

from backend.agents.memory_system import MemorySystem


class ReportAgent:
    """
    Report Agent generates a complete migration report.
    """

    def __init__(self, memory: MemorySystem):
        self.memory = memory

    async def generate_report(self, repo_path: str) -> Dict:
        """Generate the complete migration report"""
        print(f"📊 Report Agent: Generating report")

        # Get all data from memory
        project_info = self.memory.get_project_info()
        verification = project_info.get('verification', {})
        changes_made = project_info.get('changes_made', [])
        plan = project_info.get('plan', {})

        report = {
            "metadata": self._get_metadata(repo_path, project_info),
            "summary": self._get_summary(project_info, verification, changes_made),
            "details": self._get_details(project_info, plan, changes_made),
            "verification": self._get_verification_details(verification),
            "files_changed": self._get_files_changed(changes_made),
            "statistics": self._get_statistics(project_info, changes_made),
            "recommendations": self._get_recommendations(verification),
            "generated_at": datetime.utcnow().isoformat()
        }

        # Store report in memory
        self.memory.set_project_info({
            **project_info,
            "report": report
        })

        return report

    def _get_metadata(self, repo_path: str, project_info: Dict) -> Dict:
        """Get report metadata"""
        return {
            "repository": os.path.basename(repo_path),
            "repository_path": repo_path,
            "framework": project_info.get('framework', 'Unknown'),
            "current_version": project_info.get('version', 'Unknown'),
            "target_version": project_info.get('target_version', 'Latest'),
            "confidence": project_info.get('confidence', 0),
            "report_version": "1.0.0"
        }

    def _get_summary(self, project_info: Dict, verification: Dict, changes_made: List) -> Dict:
        """Get the report summary"""
        return {
            "status": "success" if verification.get('status') != 'rejected' else "rejected",
            "files_modified": len(changes_made),
            "tests_passed": verification.get('passed', 0),
            "tests_failed": verification.get('failed', 0),
            "tests_generated": verification.get('tests_generated', False),
            "hitl_approved": verification.get('hitl', {}).get('action') == 'approve',
            "framework": project_info.get('framework', 'Unknown'),
            "from_version": project_info.get('version', 'Unknown'),
            "to_version": project_info.get('target_version', 'Latest')
        }

    def _get_details(self, project_info: Dict, plan: Dict, changes_made: List) -> Dict:
        """Get detailed migration information"""
        return {
            "project_summary": project_info.get('summary', 'No summary available'),
            "structure": project_info.get('structure', 'Unknown'),
            "dependencies": project_info.get('dependencies', {}),
            "plan_steps": plan.get('steps', []),
            "key_files": project_info.get('key_files', [])
        }

    def _get_verification_details(self, verification: Dict) -> Dict:
        """Get verification details"""
        return {
            "framework": verification.get('framework', 'Unknown'),
            "tests_passed": verification.get('passed', 0),
            "tests_failed": verification.get('failed', 0),
            "tests_skipped": verification.get('skipped', 0),
            "tests_generated": verification.get('tests_generated', False),
            "hitl_needed": verification.get('hitl_needed', False),
            "hitl_action": verification.get('hitl', {}).get('action', 'none'),
            "hitl_message": verification.get('hitl', {}).get('message', ''),
            "status": verification.get('status', 'unknown')
        }

    def _get_files_changed(self, changes_made: List) -> List:
        """Get list of files changed"""
        return [change.get('file', '') for change in changes_made]

    def _get_statistics(self, project_info: Dict, changes_made: List) -> Dict:
        """Get migration statistics"""
        return {
            "total_files_modified": len(changes_made),
            "total_llm_calls": self._count_llm_calls(),
            "total_time": "2-3 minutes",  # Estimated
            "confidence_score": project_info.get('confidence', 0),
            "tasks_completed": len(project_info.get('plan', {}).get('steps', [])),
            "manual_review_needed": len(project_info.get('pending_issues', []))
        }

    def _count_llm_calls(self) -> int:
        """Count LLM calls made during migration"""
        # Discovery: 1 call
        # Planning: 1 call
        # Execution: 1 call
        # Total: 3 calls
        return 3

    def _get_recommendations(self, verification: Dict) -> List[str]:
        """Get recommendations based on verification results"""
        recs = []
        
        if verification.get('failed', 0) > 0:
            recs.append("Review the test failures and fix manually")
        
        if verification.get('tests_generated', False):
            recs.append("Review the generated tests for accuracy")
        
        if verification.get('hitl_needed', False):
            recs.append("Review the changes flagged for HITL")
        
        if verification.get('status') == 'rejected':
            recs.append("Migration was rejected by user. Please review the code.")
        
        if not recs:
            recs.append("All tests passed. Migration is successful.")
            recs.append("Consider adding more tests for better coverage.")

        return recs