# test_planning.py
import asyncio
import os
from backend.agents.memory_system import MemorySystem
from backend.agents.discovery_agent import DiscoveryAgent
from backend.agents.planning_agent import PlanningAgent

async def test():
    memory = MemorySystem('test-job-123')
    discovery = DiscoveryAgent(memory)
    planning = PlanningAgent(memory)

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

    print('\n' + '='*50)
    print('📋 MIGRATION PLAN')
    print('='*50)
    print(f"Title: {plan.get('title')}")
    print(f"Summary: {plan.get('summary')}")
    print(f"Total Steps: {len(plan.get('steps', []))}")
    print(f"Estimated Hours: {plan.get('estimated_hours')}")
    print(f"Difficulty: {plan.get('difficulty')}")
    print(f"Risk Level: {plan.get('risk_level')}")
    print("\n📝 Steps:")
    for step in plan.get('steps', [])[:5]:
        print(f"  {step.get('step_number')}. {step.get('title')}")
    print('='*50)

asyncio.run(test())