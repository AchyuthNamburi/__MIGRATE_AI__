# backend/agents/discovery_agent.py
"""Discovery Agent - 1 LLM call for everything"""

import os
import json
from typing import Dict, List
import fnmatch

from backend.core.llm import get_llm
from backend.tools.file_tools import FileTools
from backend.agents.memory_system import MemorySystem


class DiscoveryAgent:
    """Discovery Agent - Makes ONLY 1 LLM call per migration."""

    def __init__(self, memory: MemorySystem):
        self.memory = memory
        self.llm = get_llm()
        self.file_tools = FileTools()

    async def discover(self, repo_path: str) -> Dict:
        """ONE LLM call to discover everything."""
        print(f"🔍 Discovery Agent: Analyzing {repo_path}")

        # 1. Get file tree
        file_tree = self._get_file_tree(repo_path)
        print(f"   📂 Found {len(file_tree)} files")

        # 2. Read key files (README, requirements, etc.)
        key_files = self._get_key_files(repo_path)
        file_contents = {}
        for f in key_files:
            content = self.file_tools.read_file(os.path.join(repo_path, f))
            if content:
                file_contents[f] = content[:2000]

        # 3. ONE LLM call with ALL info
        prompt = self._build_discovery_prompt(file_tree, file_contents)
        response = self.llm.invoke(prompt)

        # 4. Parse response
        result = self._parse_discovery_response(response.content)

        # 5. Store in memory
        self.memory.set_project_info(result)

        print(f"   ✅ Discovery complete! Framework: {result.get('framework')}, Confidence: {result.get('confidence')}%")

        return result

    def _get_file_tree(self, repo_path: str) -> List[str]:
        """Get list of all files"""
        files = []
        for root, dirs, filenames in os.walk(repo_path):
            if any(skip in root for skip in ['.git', '__pycache__', 'node_modules', 'venv']):
                continue
            for filename in filenames:
                if any(filename.endswith(ext) for ext in ['.py', '.js', '.jsx', '.ts', '.tsx', '.html', '.css', '.json', '.txt', '.md']):
                    files.append(os.path.relpath(os.path.join(root, filename), repo_path))
        return files[:200]

    def _get_key_files(self, repo_path: str) -> List[str]:
        """Get key files to read"""
        candidates = ['README.md', 'requirements.txt', 'package.json', 'manage.py', 'app.py', 'main.py', 'settings.py', 'pyproject.toml']
        existing = []
        for c in candidates:
            if os.path.exists(os.path.join(repo_path, c)):
                existing.append(c)
        return existing[:5]

    def _build_discovery_prompt(self, file_tree: List[str], file_contents: Dict[str, str]) -> str:
        """Build discovery prompt"""
        prompt = f"""
You are a codebase analyst. Analyze this repository and return a JSON response.

FILE TREE:
{json.dumps(file_tree[:50], indent=2)}

KEY FILE CONTENTS:
"""

        for path, content in file_contents.items():
            prompt += f"\n--- {path} ---\n{content[:1000]}\n"

        prompt += """
Return JSON with:
{
    "framework": "Django, React, FastAPI, Flask, Pandas, etc.",
    "version": "version number",
    "confidence": 0-100,
    "reasoning": "why you identified this",
    "dependencies": {"python": [], "node": []},
    "structure": "brief description of project structure",
    "key_files": [],
    "has_tests": true/false,
    "summary": "brief summary of what this project does"
}

Return ONLY valid JSON.
"""
        return prompt

    def _parse_discovery_response(self, response: str) -> Dict:
        """Parse discovery response"""
        try:
            response = response.strip()
            if '```json' in response:
                response = response.split('```json')[1].split('```')[0]
            elif '```' in response:
                response = response.split('```')[1].split('```')[0]
            return json.loads(response)
        except:
            return {
                "framework": "Unknown",
                "version": "Unknown",
                "confidence": 0,
                "reasoning": "Failed to parse response",
                "dependencies": {},
                "structure": "Unknown",
                "key_files": [],
                "has_tests": False,
                "summary": "Unable to analyze"
            }