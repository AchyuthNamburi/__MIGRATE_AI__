# test_repair.py
import asyncio
import os
from backend.agents.memory_system import MemorySystem
from backend.agents.discovery_agent import DiscoveryAgent
from backend.agents.planning_agent import PlanningAgent
from backend.agents.execution_agent import ExecutionAgent
from backend.agents.verification_agent import VerificationAgent
from backend.agents.repair_agent import RepairAgent

async def test():
    memory = MemorySystem('test-job-123')
    discovery = DiscoveryAgent(memory)
    planning = PlanningAgent(memory)
    execution = ExecutionAgent(memory)
    verification = VerificationAgent(memory)
    repair = RepairAgent(memory)

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
    await execution.execute(repo_path, plan)

    # Step 4: Verify
    print("\n🧪 Running Verification Agent...")
    verification_result = await verification.verify(repo_path)

    # Step 5: Repair (if needed)
    if verification_result.get('failed', 0) > 0 or verification_result.get('no_tests', False):
        print("\n🔧 Running Repair Agent...")
        repair_result = await repair.repair(repo_path, verification_result)

        print('\n' + '='*50)
        print('📋 REPAIR RESULTS')
        print('='*50)
        print(f"Status: {repair_result.get('status')}")
        print(f"Attempts: {repair_result.get('attempts', 0)}")
        if repair_result.get('history'):
            print(f"History: {len(repair_result.get('history', []))} fixes applied")
        print('='*50)
    else:
        print("\n✅ No repairs needed. All tests passed!")

asyncio.run(test())