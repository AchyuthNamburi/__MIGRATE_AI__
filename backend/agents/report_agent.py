# backend/agents/report_agent.py
"""Report Agent - Generates migration reports"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

class ReportAgent:
    """Generates comprehensive migration reports"""
    
    def __init__(self, repo_path: str, analysis: Dict, plan: Dict, migration_result: Dict, verification_result: Dict):
        self.repo_path = repo_path
        self.analysis = analysis
        self.plan = plan
        self.migration_result = migration_result
        self.verification_result = verification_result
        self.report = {}
    
    async def generate_report(self) -> Dict:
        """Generate complete migration report"""
        logger.info(f"📊 Generating report for: {self.repo_path}")
        
        self.report = {
            "metadata": self._get_metadata(),
            "summary": self._get_summary(),
            "analysis": self._get_analysis_summary(),
            "plan": self._get_plan_summary(),
            "migration": self._get_migration_summary(),
            "verification": self._get_verification_summary(),
            "changes": self._get_changes_details(),
            "recommendations": self._get_recommendations(),
            "generated_at": datetime.utcnow().isoformat()
        }
        
        self.report["formats"] = {
            "json": await self._generate_json(),
            "markdown": await self._generate_markdown(),
            "html": await self._generate_html()
        }
        
        return self.report
    
    def _get_metadata(self) -> Dict:
        return {
            "repository": os.path.basename(self.repo_path),
            "repository_path": self.repo_path,
            "framework": self.analysis.get("framework", "Unknown"),
            "current_version": self.analysis.get("current_version", "Unknown"),
            "target_version": self.analysis.get("target_version", "Unknown"),
            "report_version": "1.0.0"
        }
    
    def _get_summary(self) -> Dict:
        migration = self.migration_result or {}
        verification = self.verification_result or {}
        summary = verification.get("summary", {})
        
        return {
            "status": "success" if not migration.get("errors") else "failed",
            "total_steps": migration.get("total_steps", 0),
            "completed_steps": migration.get("completed_steps", 0),
            "files_modified": migration.get("modified_files", 0),
            "changes_made": migration.get("changes", 0),
            "errors": len(migration.get("errors", [])),
            "verification_status": summary.get("status", "unknown"),
            "tests_passed": summary.get("tests_passed", 0),
            "tests_failed": summary.get("tests_failed", 0),
            "build_success": summary.get("build_success", False)
        }
    
    def _get_analysis_summary(self) -> Dict:
        stats = self.analysis.get("stats", {})
        return {
            "language": self.analysis.get("language", "Unknown"),
            "framework": self.analysis.get("framework", "Unknown"),
            "current_version": self.analysis.get("current_version", "Unknown"),
            "target_version": self.analysis.get("target_version", "Unknown"),
            "total_files": stats.get("total_files", 0),
            "total_lines": stats.get("total_lines", 0),
            "python_files": stats.get("python_files", 0),
            "js_files": stats.get("js_files", 0),
            "html_files": stats.get("html_files", 0),
            "css_files": stats.get("css_files", 0),
            "dependencies": len(self.analysis.get("dependencies", {}).get("python", []))
        }
    
    def _get_plan_summary(self) -> Dict:
        steps = self.plan.get("steps", [])
        return {
            "total_steps": len(steps),
            "completed_steps": len([s for s in steps if s.get("step_number", 0) <= self.migration_result.get("completed_steps", 0)]),
            "estimated_hours": self.plan.get("estimated_effort", {}).get("estimated_hours", 0),
            "difficulty": self.plan.get("summary", {}).get("difficulty", "Unknown"),
            "breaking_changes": len(self.plan.get("breaking_changes", []))
        }
    
    def _get_migration_summary(self) -> Dict:
        return {
            "status": self.migration_result.get("status", "unknown"),
            "total_steps": self.migration_result.get("total_steps", 0),
            "completed_steps": self.migration_result.get("completed_steps", 0),
            "modified_files": self.migration_result.get("modified_files", 0),
            "changes": self.migration_result.get("changes", 0),
            "errors": self.migration_result.get("errors", []),
            "backup_path": self.migration_result.get("backup_path", ""),
            "modified_files_list": self.migration_result.get("modified_files_list", [])
        }
    
    def _get_verification_summary(self) -> Dict:
        summary = self.verification_result.get("summary", {})
        return {
            "status": summary.get("status", "unknown"),
            "tests_passed": summary.get("tests_passed", 0),
            "tests_failed": summary.get("tests_failed", 0),
            "tests_skipped": summary.get("tests_skipped", 0),
            "build_success": summary.get("build_success", False),
            "total_checks": summary.get("total_checks", 0),
            "passed_checks": summary.get("passed_checks", 0),
            "failed_checks": summary.get("failed_checks", 0),
            "details": self.verification_result.get("details", [])
        }
    
    def _get_changes_details(self) -> List[Dict]:
        changes = self.migration_result.get("changes_summary", {})
        return [
            {"type": change_type, "count": count}
            for change_type, count in changes.items()
        ]
    
    def _get_recommendations(self) -> List[str]:
        recommendations = [
            "Review the changes before deploying",
            "Run tests manually if automated tests were not found",
            "Check for any manual fixes needed",
            "Update documentation to reflect changes",
            "Commit the changes to version control"
        ]
        
        if self.verification_result.get("summary", {}).get("status") == "no_tests":
            recommendations.append("Add tests to verify the migration worked correctly")
        
        return recommendations
    
    async def _generate_json(self) -> str:
        report_data = {
            "metadata": self.report["metadata"],
            "summary": self.report["summary"],
            "analysis": self.report["analysis"],
            "plan": self.report["plan"],
            "migration": self.report["migration"],
            "verification": self.report["verification"],
            "recommendations": self.report["recommendations"],
            "generated_at": self.report["generated_at"]
        }
        return json.dumps(report_data, indent=2)
    
    async def _generate_markdown(self) -> str:
        md = f"""# Migration Report

## 📊 Summary

| Metric | Value |
|--------|-------|
| **Status** | {self.report['summary']['status']} |
| **Framework** | {self.report['metadata']['framework']} |
| **From Version** | {self.report['metadata']['current_version']} |
| **To Version** | {self.report['metadata']['target_version']} |
| **Files Modified** | {self.report['summary']['files_modified']} |
| **Changes Made** | {self.report['summary']['changes_made']} |
| **Tests Passed** | {self.report['summary']['tests_passed']} |
| **Tests Failed** | {self.report['summary']['tests_failed']} |
| **Build Success** | {self.report['summary']['build_success']} |

---

## 📁 Repository Analysis

- **Language**: {self.report['analysis']['language']}
- **Framework**: {self.report['analysis']['framework']}
- **Current Version**: {self.report['analysis']['current_version']}
- **Target Version**: {self.report['analysis']['target_version']}
- **Total Files**: {self.report['analysis']['total_files']}
- **Total Lines**: {self.report['analysis']['total_lines']}

---

## 📋 Migration Plan

- **Total Steps**: {self.report['plan']['total_steps']}
- **Completed Steps**: {self.report['plan']['completed_steps']}
- **Estimated Hours**: {self.report['plan']['estimated_hours']}
- **Difficulty**: {self.report['plan']['difficulty']}
- **Breaking Changes**: {self.report['plan']['breaking_changes']}

---

## ✅ Changes Made

"""
        for change in self.report.get('changes', []):
            md += f"- **{change['type']}**: {change['count']} changes\n"
        
        md += f"""

## 📝 Verification Results

- **Status**: {self.report['verification']['status']}
- **Tests Passed**: {self.report['verification']['tests_passed']}
- **Tests Failed**: {self.report['verification']['tests_failed']}
- **Build Success**: {self.report['verification']['build_success']}
- **Checks Passed**: {self.report['verification']['passed_checks']}/{self.report['verification']['total_checks']}

## 📌 Recommendations

"""
        for rec in self.report.get('recommendations', []):
            md += f"- {rec}\n"
        
        md += f"""

---
*Report generated at {self.report['generated_at']}*
"""
        return md
    
    async def _generate_html(self) -> str:
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Migration Report - {self.report['metadata']['repository']}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; background: #f5f5f5; }}
        .container {{ background: white; padding: 30px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
        h1 {{ color: #1a1a2e; border-bottom: 2px solid #4f46e5; padding-bottom: 10px; }}
        .status {{ display: inline-block; padding: 4px 12px; border-radius: 20px; font-weight: 600; }}
        .status-success {{ background: #e8f5e9; color: #4caf50; }}
        .status-failed {{ background: #fce4ec; color: #f44336; }}
        .status-unknown {{ background: #fff3e0; color: #ff9800; }}
        table {{ width: 100%; border-collapse: collapse; margin: 16px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #e0e0e0; }}
        th {{ background: #f8f9fa; font-weight: 600; }}
        .section {{ margin: 24px 0; padding: 16px; background: #f8f9fa; border-radius: 8px; }}
        .section h2 {{ margin-top: 0; color: #1a1a2e; font-size: 18px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 Migration Report</h1>
        <p><strong>Repository:</strong> {self.report['metadata']['repository']}</p>
        <p><strong>Generated:</strong> {self.report['generated_at']}</p>

        <div class="section">
            <h2>📊 Summary</h2>
            <table>
                <tr><td><strong>Status</strong></td>
                    <td><span class="status status-{self.report['summary']['status']}">{self.report['summary']['status']}</span></td></tr>
                <tr><td><strong>Framework</strong></td><td>{self.report['metadata']['framework']}</td></tr>
                <tr><td><strong>From → To</strong></td><td>{self.report['metadata']['current_version']} → {self.report['metadata']['target_version']}</td></tr>
                <tr><td><strong>Files Modified</strong></td><td>{self.report['summary']['files_modified']}</td></tr>
                <tr><td><strong>Changes Made</strong></td><td>{self.report['summary']['changes_made']}</td></tr>
                <tr><td><strong>Tests Passed</strong></td><td>{self.report['summary']['tests_passed']}</td></tr>
                <tr><td><strong>Build Success</strong></td><td>{'✅' if self.report['summary']['build_success'] else '❌'}</td></tr>
            </table>
        </div>

        <div class="section">
            <h2>📁 Repository Analysis</h2>
            <table>
                <tr><td><strong>Language</strong></td><td>{self.report['analysis']['language']}</td></tr>
                <tr><td><strong>Total Files</strong></td><td>{self.report['analysis']['total_files']}</td></tr>
                <tr><td><strong>Total Lines</strong></td><td>{self.report['analysis']['total_lines']}</td></tr>
            </table>
        </div>

        <div class="section">
            <h2>📋 Migration Plan</h2>
            <table>
                <tr><td><strong>Total Steps</strong></td><td>{self.report['plan']['total_steps']}</td></tr>
                <tr><td><strong>Completed</strong></td><td>{self.report['plan']['completed_steps']}</td></tr>
                <tr><td><strong>Difficulty</strong></td><td>{self.report['plan']['difficulty']}</td></tr>
            </table>
        </div>

        <div class="section">
            <h2>✅ Changes Made</h2>
            <ul>
"""
        for change in self.report.get('changes', []):
            html += f"<li><strong>{change['type']}</strong>: {change['count']} changes</li>"
        
        html += f"""
            </ul>
        </div>

        <div class="section">
            <h2>📝 Verification Results</h2>
            <table>
                <tr><td><strong>Status</strong></td><td><span class="status status-{self.report['verification']['status']}">{self.report['verification']['status']}</span></td></tr>
                <tr><td><strong>Tests Passed</strong></td><td>{self.report['verification']['tests_passed']}</td></tr>
                <tr><td><strong>Build Success</strong></td><td>{'✅' if self.report['verification']['build_success'] else '❌'}</td></tr>
            </table>
        </div>

        <div class="section">
            <h2>📌 Recommendations</h2>
            <ul>
"""
        for rec in self.report.get('recommendations', []):
            html += f"<li>{rec}</li>"
        
        html += f"""
            </ul>
        </div>

        <p style="color: #6c757d; font-size: 12px; margin-top: 30px;">Report generated by AI Migration Agent</p>
    </div>
</body>
</html>
"""
        return html
