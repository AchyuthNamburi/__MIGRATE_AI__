# test_discovery.py
import asyncio
import os
from backend.agents.memory_system import MemorySystem
from backend.agents.discovery_agent import DiscoveryAgent

async def test():
    # Set your Groq API key
    memory = MemorySystem('test-job-123')
    agent = DiscoveryAgent(memory)

    # Test on a sample repo (djangox - imported earlier)
    repo_path = '/tmp/migration_agent/repos/478f8ab9-7c5c-4db0-8e8e-d5113d026dff/djangox'

    if not os.path.exists(repo_path):
        print('❌ Repo not found. Please clone a repo first.')
        return

    result = await agent.discover(repo_path)

    print('\n' + '='*50)
    print('📋 DISCOVERY RESULTS (LLM-Powered)')
    print('='*50)
    print(f"Framework: {result.get('framework')}")
    print(f"Version: {result.get('version')}")
    print(f"Confidence: {result.get('confidence')}%")
    print(f"Reasoning: {result.get('reasoning')}")
    print(f"Dependencies: {len(result.get('dependencies', {}).get('python', []))} packages")
    print(f"Has Tests: {result.get('has_tests')}")
    print(f"Summary: {result.get('summary')}")
    print('='*50)

asyncio.run(test())