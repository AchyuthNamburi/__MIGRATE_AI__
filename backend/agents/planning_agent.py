# backend/agents/planning_agent.py
"""Planning Agent - Creates migration plan using LLM (0 hardcoded rules)"""

import os
import json
from typing import Dict, List, Optional
from datetime import datetime

from backend.core.llm import get_llm
from backend.agents.memory_system import MemorySystem


class PlanningAgent:
    """
    Planning Agent uses LLM to create a migration plan based on Discovery results.
    No hardcoded rules for migration steps.
    """

    def __init__(self, memory: MemorySystem):
        self.memory = memory
        self.llm = get_llm()
        self.framework_rules = self._load_framework_rules()

    def _load_framework_rules(self) -> Dict:
        """Load framework rules from JSON"""
        rules_path = os.path.join(os.path.dirname(__file__), '..', 'rules', 'framework_rules.json')
        try:
            with open(rules_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    async def plan(self, discovery_result: Dict) -> Dict:
        """
        Create a migration plan based on discovery results.
        """
        print(f"📋 Planning Agent: Creating migration plan")

        framework = discovery_result.get('framework', 'Unknown')
        current_version = discovery_result.get('version', 'Unknown')
        confidence = discovery_result.get('confidence', 0)
        dependencies = discovery_result.get('dependencies', {})
        summary = discovery_result.get('summary', '')

        print(f"   📋 Framework: {framework}")
        print(f"   📦 Current Version: {current_version}")
        print(f"   📊 Confidence: {confidence}%")

        # Get framework-specific rules
        rules = self.framework_rules.get(framework.lower(), {})

        # Determine target version
        target_version = rules.get('to_version', self._get_latest_version(framework))

        print(f"   🎯 Target Version: {target_version}")

        # LLM generates the migration plan
        plan = await self._llm_create_plan(
            framework=framework,
            current_version=current_version,
            target_version=target_version,
            dependencies=dependencies,
            summary=summary,
            rules=rules
        )

        # Store in memory
        self.memory.set_project_info({
            **discovery_result,
            "target_version": target_version,
            "plan": plan,
            "plan_created_at": datetime.utcnow().isoformat()
        })

        print(f"   ✅ Plan created! {len(plan.get('steps', []))} steps")

        return plan

    def _get_latest_version(self, framework: str) -> str:
        """Get the latest version for a framework"""
        latest_versions = {
            "Django": "6.0.4",
            "React": "18.3.1",
            "FastAPI": "0.115.6",
            "Flask": "3.1.0",
            "Pandas": "2.2.3"
        }
        return latest_versions.get(framework, "Latest")

    async def _llm_create_plan(self, framework: str, current_version: str, target_version: str,
                               dependencies: Dict, summary: str, rules: Dict) -> Dict:
        """LLM generates a migration plan"""
        prompt = f"""
        You are a migration planning expert. Create a detailed migration plan.

        PROJECT INFORMATION:
        - Framework: {framework}
        - Current Version: {current_version}
        - Target Version: {target_version}
        - Dependencies: {json.dumps(dependencies, indent=2)[:500]}
        - Project Summary: {summary}

        FRAMEWORK-SPECIFIC KNOWLEDGE:
        {json.dumps(rules, indent=2)[:500]}

        Based on this information, create a comprehensive migration plan.

        Return a JSON object with:
        1. "title": A title for the migration plan
        2. "summary": A brief summary of the migration
        3. "steps": An array of step objects, each with:
           - "step_number": The step number
           - "title": A title for the step
           - "description": A description of what to do
           - "type": The type of step (dependency_update, code_update, config_update, database, testing)
           - "files": List of file patterns affected
           - "commands": List of commands to run (if any)
           - "verification": How to verify this step
        4. "breaking_changes": An array of breaking changes to watch for
        5. "estimated_hours": Estimated time in hours
        6. "difficulty": "easy", "medium", or "hard"
        7. "risk_level": "low", "medium", or "high"
        8. "recommendations": Array of recommendations

        Return ONLY valid JSON. No other text.
        """

        response = self.llm.invoke(prompt)

        try:
            return json.loads(response.content)
        except json.JSONDecodeError:
            # If LLM doesn't return clean JSON, try to extract
            import re
            match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except:
                    pass
            # Fallback plan
            return {
                "title": f"Migration from {framework} {current_version} to {target_version}",
                "summary": f"Upgrade {framework} from {current_version} to {target_version}",
                "steps": [
                    {
                        "step_number": 1,
                        "title": f"Update {framework} version",
                        "description": f"Update {framework} from {current_version} to {target_version}",
                        "type": "dependency_update",
                        "files": ["requirements.txt"],
                        "commands": [],
                        "verification": "Check version"
                    }
                ],
                "breaking_changes": [],
                "estimated_hours": 4,
                "difficulty": "medium",
                "risk_level": "medium",
                "recommendations": [
                    "Backup your code before starting",
                    "Run tests before and after migration"
                ]
            }