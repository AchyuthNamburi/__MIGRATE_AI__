# test_execution.py
import asyncio
import os
from backend.agents.memory_system import MemorySystem
from backend.agents.discovery_agent import DiscoveryAgent
from backend.agents.planning_agent import PlanningAgent
from backend.agents.execution_agent import ExecutionAgent

async def test():
    memory = MemorySystem('test-job-123')
    discovery = DiscoveryAgent(memory)
    planning = PlanningAgent(memory)
    execution = ExecutionAgent(memory)

    repo_path = '/tmp/migration_agent/repos/478f8ab9-7c5c-4db0-8e8e-d5113d026dff/djangox'

    if not os.path.exists(repo_path):
        print('❌ Repo not found. Please clone a repo first.')
        return

    # Step 1: Discover
    print("\n🔍 Running Discovery Agent...")
    discovery_result = await discovery.discover(repo_path)

    # Step 2: Plan
    print("\n📋 Running Planning Agent...")
    plan = await planning.plan(discovery_result)

    # Step 3: Execute
    print("\n✍️ Running Execution Agent...")
    result = await execution.execute(repo_path, plan)

    print('\n' + '='*50)
    print('📋 EXECUTION RESULTS')
    print('='*50)
    print(f"Status: {result.get('status')}")
    print(f"Files Modified: {result.get('files_modified')}")
    print('\n📝 Changes:')
    for change in result.get('changes', []):
        print(f"  - {change.get('file')} ({change.get('type')})")
    print('='*50)

asyncio.run(test())