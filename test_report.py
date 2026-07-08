# test_report.py
"""Test the full pipeline with Report Agent"""

import asyncio
import os
import json
from backend.agents.memory_system import MemorySystem
from backend.agents.discovery_agent import DiscoveryAgent
from backend.agents.planning_agent import PlanningAgent
from backend.agents.execution_agent import ExecutionAgent
from backend.agents.verification_agent import VerificationAgent
from backend.agents.report_agent import ReportAgent


async def test():
    memory = MemorySystem('test-job-123')
    discovery = DiscoveryAgent(memory)
    planning = PlanningAgent(memory)
    execution = ExecutionAgent(memory)
    verification = VerificationAgent(memory)
    report = ReportAgent(memory)

    repo_path = '/tmp/migration_agent/repos/478f8ab9-7c5c-4db0-8e8e-d5113d026dff/djangox'

    if not os.path.exists(repo_path):
        print('❌ Repo not found. Please clone a repo first.')
        return

    print("\n" + "="*60)
    print("🚀 STARTING FULL MIGRATION PIPELINE")
    print("="*60)

    # Step 1: Discover
    print("\n🔍 Running Discovery Agent...")
    discovery_result = await discovery.discover(repo_path)

    # Step 2: Plan
    print("\n📋 Running Planning Agent...")
    plan = await planning.plan(discovery_result)

    # Step 3: Execute
    print("\n✍️ Running Execution Agent...")
    await execution.execute(repo_path, plan)

    # Step 4: Verify
    print("\n🧪 Running Verification Agent...")
    verification_result = await verification.verify(repo_path)

    # Step 5: Report
    print("\n📊 Running Report Agent...")
    report_result = await report.generate_report(repo_path)

    print("\n" + "="*60)
    print("📋 MIGRATION REPORT")
    print("="*60)

    # Print report summary
    summary = report_result.get('summary', {})
    print(f"Status: {summary.get('status', 'Unknown')}")
    print(f"Framework: {summary.get('framework')}")
    print(f"From: {summary.get('from_version')} → To: {summary.get('to_version')}")
    print(f"Files Modified: {summary.get('files_modified')}")
    print(f"Tests Passed: {summary.get('tests_passed')}")
    print(f"Tests Failed: {summary.get('tests_failed')}")
    print(f"HITL Approved: {summary.get('hitl_approved')}")

    # Print changed files
    files_changed = report_result.get('files_changed', [])
    if files_changed:
        print(f"\n📝 Files Changed ({len(files_changed)}):")
        for f in files_changed[:5]:
            print(f"  - {f}")

    # Print recommendations
    recommendations = report_result.get('recommendations', [])
    if recommendations:
        print(f"\n💡 Recommendations:")
        for rec in recommendations:
            print(f"  - {rec}")

    print("\n" + "="*60)

    # Save report to file
    with open('migration_report.json', 'w') as f:
        json.dump(report_result, f, indent=2)
    print("📄 Report saved to: migration_report.json")


asyncio.run(test())