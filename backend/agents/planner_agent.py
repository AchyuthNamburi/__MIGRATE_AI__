# backend/agents/planner_agent.py
"""Migration Planner Agent - Creates migration plans"""

import logging
from typing import Dict, List, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class MigrationPlanner:
    """Creates migration plans for framework upgrades"""
    
    def __init__(self, analysis: Dict):
        self.analysis = analysis
        self.framework = analysis.get("framework", "Unknown")
        self.current_version = analysis.get("current_version", "Unknown")
        self.latest_version = analysis.get("latest_version", "Unknown")
        
        # Framework-specific migration rules
        self.migration_rules = {
            "Django": self._get_django_rules(),
            "React": self._get_react_rules(),
            "FastAPI": self._get_fastapi_rules(),
            "Flask": self._get_flask_rules()
        }
    
    async def create_plan(self) -> Dict:
        """Create a complete migration plan"""
        logger.info(f"📋 Creating migration plan for {self.framework}")
        
        plan = {
            "framework": self.framework,
            "current_version": self.current_version,
            "target_version": self.latest_version,
            "created_at": datetime.utcnow().isoformat(),
            "summary": self._create_summary(),
            "steps": self._create_steps(),
            "breaking_changes": self._get_breaking_changes(),
            "estimated_effort": self._estimate_effort(),
            "risk_assessment": self._assess_risk(),
            "recommendations": self._get_recommendations()
        }
        
        return plan
    
    def _create_summary(self) -> Dict:
        """Create a summary of the migration"""
        return {
            "title": f"Migrate from {self.framework} {self.current_version} to {self.latest_version}",
            "description": f"This plan outlines the steps to upgrade {self.framework} from version {self.current_version} to {self.latest_version}.",
            "total_steps": len(self._create_steps()),
            "estimated_time": self._estimate_time(),
            "difficulty": self._assess_difficulty()
        }
    
    def _create_steps(self) -> List[Dict]:
        """Create step-by-step migration steps"""
        steps = []
        
        if self.framework == "Django":
            steps = self._get_django_steps()
        elif self.framework == "React":
            steps = self._get_react_steps()
        elif self.framework == "FastAPI":
            steps = self._get_fastapi_steps()
        elif self.framework == "Flask":
            steps = self._get_flask_steps()
        else:
            steps = self._get_generic_steps()
        
        # Add step numbers
        for i, step in enumerate(steps, 1):
            step["step_number"] = i
        
        return steps
    
    def _get_django_steps(self) -> List[Dict]:
        """Get Django migration steps"""
        return [
            {
                "title": "Update Django version in requirements.txt",
                "description": "Change Django=={current} to Django=={target}",
                "type": "dependency_update",
                "files": ["requirements.txt"],
                "commands": [
                    f"pip install Django==4.2.10",
                    "pip install -r requirements.txt"
                ],
                "verification": "python -c 'import django; print(django.get_version())'"
            },
            {
                "title": "Update URL patterns",
                "description": "Replace deprecated url() with path() or re_path()",
                "type": "code_update",
                "files": ["**/urls.py"],
                "pattern": "url(",
                "replacement": "path(",
                "verification": "grep -r 'url(' --include='*.py'"
            },
            {
                "title": "Update middleware configuration",
                "description": "Replace MIDDLEWARE_CLASSES with MIDDLEWARE",
                "type": "config_update",
                "files": ["settings.py"],
                "pattern": "MIDDLEWARE_CLASSES",
                "replacement": "MIDDLEWARE",
                "verification": "grep -r 'MIDDLEWARE_CLASSES' --include='*.py'"
            },
            {
                "title": "Update default settings",
                "description": "Update deprecated settings like DEFAULT_CONTENT_TYPE",
                "type": "config_update",
                "files": ["settings.py"],
                "pattern": "DEFAULT_CONTENT_TYPE",
                "replacement": "Removed - use HttpResponse.setdefault()",
                "verification": "grep -r 'DEFAULT_CONTENT_TYPE' --include='*.py'"
            },
            {
                "title": "Update models and queries",
                "description": "Update deprecated model methods and query syntax",
                "type": "code_update",
                "files": ["**/models.py"],
                "patterns": [
                    {"old": ".objects.get_or_create(", "new": ".objects.get_or_create("},
                    {"old": ".objects.filter(", "new": ".objects.filter("}
                ],
                "verification": "python manage.py check"
            },
            {
                "title": "Update template filters",
                "description": "Update deprecated template filters",
                "type": "code_update",
                "files": ["**/*.html"],
                "patterns": [
                    {"old": "{% load %}", "new": "{% load %}"}
                ],
                "verification": "python manage.py check --deploy"
            },
            {
                "title": "Run migrations",
                "description": "Apply database migrations",
                "type": "database",
                "commands": [
                    "python manage.py makemigrations",
                    "python manage.py migrate"
                ],
                "verification": "python manage.py showmigrations"
            },
            {
                "title": "Run tests",
                "description": "Verify everything works",
                "type": "testing",
                "commands": ["python manage.py test"],
                "verification": "All tests pass"
            }
        ]
    
    def _get_react_steps(self) -> List[Dict]:
        """Get React migration steps"""
        return [
            {
                "title": "Update React version in package.json",
                "description": "Change react and react-dom versions",
                "type": "dependency_update",
                "files": ["package.json"],
                "commands": [
                    "npm install react@18 react-dom@18",
                    "npm install"
                ],
                "verification": "npm list react"
            },
            {
                "title": "Update ReactDOM.render to createRoot",
                "description": "Replace ReactDOM.render with createRoot API",
                "type": "code_update",
                "files": ["**/*.js", "**/*.jsx"],
                "pattern": "ReactDOM.render(",
                "replacement": "root.render(",
                "verification": "grep -r 'ReactDOM.render' --include='*.js'"
            },
            {
                "title": "Update component lifecycle methods",
                "description": "Update deprecated lifecycle methods",
                "type": "code_update",
                "files": ["**/*.js", "**/*.jsx"],
                "patterns": [
                    {"old": "componentWillMount", "new": "UNSAFE_componentWillMount or useEffect"},
                    {"old": "componentWillReceiveProps", "new": "UNSAFE_componentWillReceiveProps or getDerivedStateFromProps"},
                    {"old": "componentWillUpdate", "new": "UNSAFE_componentWillUpdate or getSnapshotBeforeUpdate"}
                ],
                "verification": "grep -r 'componentWill' --include='*.js'"
            },
            {
                "title": "Run tests",
                "description": "Verify everything works",
                "type": "testing",
                "commands": ["npm test"],
                "verification": "All tests pass"
            }
        ]
    
    def _get_fastapi_steps(self) -> List[Dict]:
        """Get FastAPI migration steps"""
        return [
            {
                "title": "Update FastAPI version",
                "description": "Update FastAPI to latest version",
                "type": "dependency_update",
                "files": ["requirements.txt"],
                "commands": [
                    "pip install fastapi==0.109.0",
                    "pip install -r requirements.txt"
                ],
                "verification": "python -c 'import fastapi; print(fastapi.__version__)'"
            },
            {
                "title": "Update Pydantic to V2",
                "description": "Update Pydantic to version 2",
                "type": "dependency_update",
                "files": ["requirements.txt"],
                "commands": [
                    "pip install pydantic==2.5.0",
                    "pip install pydantic-settings==2.1.0"
                ],
                "verification": "python -c 'import pydantic; print(pydantic.__version__)'"
            },
            {
                "title": "Update Pydantic models",
                "description": "Update Pydantic models for V2 compatibility",
                "type": "code_update",
                "files": ["**/*.py"],
                "patterns": [
                    {"old": "from pydantic import BaseModel", "new": "from pydantic import BaseModel"},
                    {"old": "@validator", "new": "@field_validator"},
                    {"old": "class Config:", "new": "class Config:"}
                ],
                "verification": "grep -r '@validator' --include='*.py'"
            },
            {
                "title": "Run tests",
                "description": "Verify everything works",
                "type": "testing",
                "commands": ["pytest"],
                "verification": "All tests pass"
            }
        ]
    
    def _get_flask_steps(self) -> List[Dict]:
        """Get Flask migration steps"""
        return [
            {
                "title": "Update Flask version",
                "description": "Update Flask to latest version",
                "type": "dependency_update",
                "files": ["requirements.txt"],
                "commands": [
                    "pip install flask==3.0.0",
                    "pip install -r requirements.txt"
                ],
                "verification": "python -c 'import flask; print(flask.__version__)'"
            },
            {
                "title": "Update deprecated methods",
                "description": "Update deprecated Flask methods",
                "type": "code_update",
                "files": ["**/*.py"],
                "patterns": [
                    {"old": "@app.route(", "new": "@app.route("}
                ],
                "verification": "grep -r 'deprecated' --include='*.py'"
            },
            {
                "title": "Run tests",
                "description": "Verify everything works",
                "type": "testing",
                "commands": ["pytest"],
                "verification": "All tests pass"
            }
        ]
    
    def _get_generic_steps(self) -> List[Dict]:
        """Get generic migration steps"""
        return [
            {
                "title": "Update dependencies",
                "description": "Update all dependencies to latest versions",
                "type": "dependency_update",
                "files": ["requirements.txt", "package.json"],
                "commands": ["pip install -r requirements.txt", "npm install"],
                "verification": "Check dependency versions"
            },
            {
                "title": "Run tests",
                "description": "Verify everything works",
                "type": "testing",
                "commands": ["pytest", "npm test"],
                "verification": "All tests pass"
            }
        ]
    
    def _get_breaking_changes(self) -> List[Dict]:
        """Get breaking changes between versions"""
        breaking_changes = []
        
        if self.framework == "Django":
            breaking_changes = [
                {
                    "change": "URL configuration",
                    "description": "url() is deprecated, use path() or re_path()",
                    "impact": "high",
                    "migration": "Replace url() with path() or re_path()"
                },
                {
                    "change": "Middleware",
                    "description": "MIDDLEWARE_CLASSES replaced with MIDDLEWARE",
                    "impact": "medium",
                    "migration": "Update settings.py"
                },
                {
                    "change": "Default settings",
                    "description": "Some default settings have been removed",
                    "impact": "low",
                    "migration": "Review and update settings"
                }
            ]
        elif self.framework == "React":
            breaking_changes = [
                {
                    "change": "ReactDOM.render",
                    "description": "ReactDOM.render is deprecated, use createRoot",
                    "impact": "high",
                    "migration": "Replace ReactDOM.render with createRoot"
                },
                {
                    "change": "Lifecycle methods",
                    "description": "componentWillMount, componentWillReceiveProps, componentWillUpdate are deprecated",
                    "impact": "medium",
                    "migration": "Replace with new lifecycle methods or hooks"
                }
            ]
        elif self.framework == "FastAPI":
            breaking_changes = [
                {
                    "change": "Pydantic V2",
                    "description": "Pydantic V2 has breaking changes",
                    "impact": "high",
                    "migration": "Update Pydantic models for V2"
                }
            ]
        
        return breaking_changes
    
    def _estimate_effort(self) -> Dict:
        """Estimate effort for migration"""
        # Simple estimation based on file count and framework
        file_count = self.analysis.get("stats", {}).get("total_files", 0)
        
        if file_count < 100:
            effort = "low"
            hours = 4
        elif file_count < 500:
            effort = "medium"
            hours = 16
        elif file_count < 1000:
            effort = "high"
            hours = 40
        else:
            effort = "very_high"
            hours = 80
        
        return {
            "effort": effort,
            "estimated_hours": hours,
            "estimated_days": round(hours / 8, 1),
            "complexity": "medium"
        }
    
    def _estimate_time(self) -> str:
        """Estimate time for migration"""
        effort = self._estimate_effort()
        hours = effort["estimated_hours"]
        if hours < 8:
            return "Less than a day"
        elif hours < 24:
            return f"~{hours / 8:.1f} days"
        else:
            return f"~{hours / 8:.1f} days"
    
    def _assess_difficulty(self) -> str:
        """Assess difficulty of migration"""
        file_count = self.analysis.get("stats", {}).get("total_files", 0)
        if file_count < 100:
            return "Easy"
        elif file_count < 500:
            return "Medium"
        else:
            return "Hard"
    
    def _assess_risk(self) -> Dict:
        """Assess migration risk"""
        breaking_changes = self._get_breaking_changes()
        
        high_impact = sum(1 for change in breaking_changes if change.get("impact") == "high")
        
        if high_impact > 2:
            risk = "high"
        elif high_impact > 0:
            risk = "medium"
        else:
            risk = "low"
        
        return {
            "level": risk,
            "high_impact_changes": high_impact,
            "total_breaking_changes": len(breaking_changes),
            "mitigation": "Test thoroughly and have a rollback plan"
        }
    
    def _get_recommendations(self) -> List[str]:
        """Get migration recommendations"""
        recommendations = [
            "Backup your code before starting",
            "Run tests before and after migration",
            "Migrate one step at a time",
            "Use version control (git) for tracking changes",
            "Test in a staging environment first",
            "Document all changes made",
            "Have a rollback plan ready"
        ]
        
        if self.framework == "Django":
            recommendations.append("Use django-upgrade to automate some changes")
            recommendations.append("Check Django release notes for specific changes")
        elif self.framework == "React":
            recommendations.append("Use react-codemod for automated refactoring")
            recommendations.append("Check React upgrade guide for detailed steps")
        
        return recommendations
    
    def _get_django_rules(self) -> List[Dict]:
        """Get Django migration rules"""
        return [
            {"pattern": "url(", "replacement": "path(", "files": ["**/urls.py"]},
            {"pattern": "MIDDLEWARE_CLASSES", "replacement": "MIDDLEWARE", "files": ["settings.py"]},
            {"pattern": "DEFAULT_CONTENT_TYPE", "replacement": "REMOVED", "files": ["settings.py"]}
        ]
    
    def _get_react_rules(self) -> List[Dict]:
        """Get React migration rules"""
        return [
            {"pattern": "ReactDOM.render(", "replacement": "root.render(", "files": ["**/*.js", "**/*.jsx"]},
            {"pattern": "componentWillMount", "replacement": "UNSAFE_componentWillMount", "files": ["**/*.js", "**/*.jsx"]},
            {"pattern": "componentWillReceiveProps", "replacement": "UNSAFE_componentWillReceiveProps", "files": ["**/*.js", "**/*.jsx"]},
            {"pattern": "componentWillUpdate", "replacement": "UNSAFE_componentWillUpdate", "files": ["**/*.js", "**/*.jsx"]}
        ]
    
    def _get_fastapi_rules(self) -> List[Dict]:
        """Get FastAPI migration rules"""
        return [
            {"pattern": "from pydantic import", "replacement": "from pydantic.v1 import", "files": ["**/*.py"]},
            {"pattern": "@validator", "replacement": "@field_validator", "files": ["**/*.py"]}
        ]
    
    def _get_flask_rules(self) -> List[Dict]:
        """Get Flask migration rules"""
        return [
            {"pattern": "app.before_first_request", "replacement": "app.before_request", "files": ["**/*.py"]}
        ]