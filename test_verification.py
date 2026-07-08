# test_verification.py
import asyncio
import os
from backend.agents.memory_system import MemorySystem
from backend.agents.discovery_agent import DiscoveryAgent
from backend.agents.planning_agent import PlanningAgent
from backend.agents.execution_agent import ExecutionAgent
from backend.agents.verification_agent import VerificationAgent

async def test():
    memory = MemorySystem('test-job-123')
    discovery = DiscoveryAgent(memory)
    planning = PlanningAgent(memory)
    execution = ExecutionAgent(memory)
    verification = VerificationAgent(memory)

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
    result = await verification.verify(repo_path)

    print('\n' + '='*50)
    print('📋 VERIFICATION RESULTS')
    print('='*50)
    print(f"Test Framework: {result.get('framework')}")
    print(f"Tests Passed: {result.get('passed')}")
    print(f"Tests Failed: {result.get('failed')}")
    print(f"Success: {result.get('success')}")
    
    if result.get('failure_analysis'):
        print("\n🔍 Failure Analysis:")
        print(f"  Summary: {result['failure_analysis'].get('summary')}")
    print('='*50)

asyncio.run(test())