import asyncio
import os
import sys
sys.path.insert(0, os.getcwd())

from backend.agents.analyzer_agent import RepositoryAnalyzer
from backend.agents.planner_agent import MigrationPlanner
from backend.agents.migrator_agent import CodeMigrator
from backend.agents.verification_agent import VerificationAgent
from backend.agents.report_agent import ReportAgent

async def main():
    repo_path = "/tmp/migration_agent/repos/478f8ab9-7c5c-4db0-8e8e-d5113d026dff/djangox"
    
    print("🔍 Analyzing...")
    analyzer = RepositoryAnalyzer(repo_path)
    analysis = await analyzer.analyze()
    
    print("📋 Planning...")
    planner = MigrationPlanner(analysis)
    plan = await planner.create_plan()
    
    print("🚀 Migrating...")
    migrator = CodeMigrator(repo_path, plan)
    migration_result = await migrator.execute()
    
    print("✅ Verifying...")
    verifier = VerificationAgent(repo_path)
    verification_result = await verifier.verify()
    
    print("📊 Generating Report...")
    report_agent = ReportAgent(repo_path, analysis, plan, migration_result, verification_result)
    report = await report_agent.generate_report()
    
    print("\n" + "="*50)
    print("📊 REPORT SUMMARY")
    print("="*50)
    print(f"Status: {report.get('summary', {}).get('status')}")
    print(f"Files Modified: {report.get('summary', {}).get('files_modified')}")
    print(f"Changes Made: {report.get('summary', {}).get('changes_made')}")
    print(f"Tests Passed: {report.get('summary', {}).get('tests_passed')}")
    print(f"Build Success: {report.get('summary', {}).get('build_success')}")
    print("="*50)

if __name__ == "__main__":
    asyncio.run(main())
