# backend/agents/analyzer_agent.py
"""Repository Analyzer Agent - Detects framework, version, and migration needs"""

import os
import re
import json
import ast
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

class RepositoryAnalyzer:
    """Analyzes repository to detect framework, version, and migration needs"""
    
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.analysis = {
            "language": None,
            "framework": None,
            "current_version": None,
            "latest_version": None,
            "dependencies": {},
            "files": [],
            "migration_opportunities": [],
            "stats": {
                "total_files": 0,
                "total_lines": 0,
                "python_files": 0,
                "js_files": 0,
                "html_files": 0,
                "css_files": 0
            }
        }
    
    async def analyze(self) -> Dict:
        """Main analysis method"""
        logger.info(f"🔍 Analyzing repository: {self.repo_path}")
        
        # Step 1: Detect language
        self.analysis["language"] = self.detect_language()
        
        # Step 2: Detect framework
        self.analysis["framework"] = self.detect_framework()
        
        # Step 3: Detect versions
        version_info = self.detect_versions()
        self.analysis["current_version"] = version_info.get("current")
        self.analysis["latest_version"] = version_info.get("latest")
        
        # Step 4: Parse dependencies
        self.analysis["dependencies"] = self.parse_dependencies()
        
        # Step 5: Analyze files
        self.analysis["files"] = self.analyze_files()
        
        # Step 6: Find migration opportunities
        self.analysis["migration_opportunities"] = self.find_migration_opportunities()
        
        # Step 7: Calculate stats
        self.analysis["stats"] = self.calculate_stats()
        
        logger.info(f"✅ Analysis complete: {self.analysis['framework']} v{self.analysis['current_version']}")
        return self.analysis
    
    def detect_language(self) -> str:
        """Detect primary language of the repository"""
        languages = {
            "python": 0,
            "javascript": 0,
            "java": 0,
            "go": 0,
            "rust": 0
        }
        
        for root, dirs, files in os.walk(self.repo_path):
            # Skip common directories
            if any(skip in root for skip in ['.git', '__pycache__', 'node_modules', 'venv', 'env']):
                continue
                
            for file in files:
                if file.endswith('.py'):
                    languages["python"] += 1
                elif file.endswith(('.js', '.jsx', '.ts', '.tsx')):
                    languages["javascript"] += 1
                elif file.endswith('.java'):
                    languages["java"] += 1
                elif file.endswith('.go'):
                    languages["go"] += 1
                elif file.endswith('.rs'):
                    languages["rust"] += 1
        
        if languages["python"] > 0:
            return "Python"
        elif languages["javascript"] > 0:
            return "JavaScript"
        elif languages["java"] > 0:
            return "Java"
        elif languages["go"] > 0:
            return "Go"
        elif languages["rust"] > 0:
            return "Rust"
        else:
            return "Unknown"
    
    def detect_framework(self) -> str:
    # Check for Django source
        if os.path.exists(os.path.join(self.repo_path, 'django')):
            return "Django"
        
        # Check for Django project
        if os.path.exists(os.path.join(self.repo_path, 'manage.py')):
            return "Django"
        
        # Check for FastAPI
        for root, dirs, files in os.walk(self.repo_path):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        if 'from fastapi import' in content or 'import fastapi' in content:
                            return "FastAPI"
                        if 'from flask import' in content or 'import flask' in content:
                            return "Flask"
        
        # Check for React
        if os.path.exists(os.path.join(self.repo_path, 'package.json')):
            with open(os.path.join(self.repo_path, 'package.json'), 'r') as f:
                try:
                    pkg = json.load(f)
                    deps = pkg.get('dependencies', {})
                    if 'react' in deps:
                        return "React"
                    if 'vue' in deps:
                        return "Vue"
                    if '@angular/core' in deps:
                        return "Angular"
                except:
                    pass
        
        return "Unknown"
    
    def detect_versions(self) -> Dict[str, str]:
        """Detect current and latest versions"""
        framework = self.analysis["framework"]
        version_info = {"current": None, "latest": None}
        
        if framework == "Django":
            # Check requirements.txt
            req_path = os.path.join(self.repo_path, 'requirements.txt')
            if os.path.exists(req_path):
                with open(req_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    match = re.search(r'Django==([\d.]+)', content)
                    if match:
                        version_info["current"] = match.group(1)
            
            # If not found, check setup.py
            setup_path = os.path.join(self.repo_path, 'setup.py')
            if os.path.exists(setup_path) and not version_info["current"]:
                with open(setup_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    match = re.search(r"version=['\"]([\d.]+)['\"]", content)
                    if match:
                        version_info["current"] = match.group(1)
            
            # Latest Django version (hardcoded for now)
            version_info["latest"] = "4.2.10"
        
        elif framework == "FastAPI":
            # Similar logic for FastAPI
            req_path = os.path.join(self.repo_path, 'requirements.txt')
            if os.path.exists(req_path):
                with open(req_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    match = re.search(r'fastapi==([\d.]+)', content)
                    if match:
                        version_info["current"] = match.group(1)
            version_info["latest"] = "0.109.0"
        
        elif framework == "React":
            package_path = os.path.join(self.repo_path, 'package.json')
            if os.path.exists(package_path):
                with open(package_path, 'r') as f:
                    try:
                        pkg = json.load(f)
                        deps = pkg.get('dependencies', {})
                        if 'react' in deps:
                            version_info["current"] = deps['react'].replace('^', '').replace('~', '')
                    except:
                        pass
            version_info["latest"] = "18.2.0"
        
        return version_info
    
    def parse_dependencies(self) -> Dict[str, List[str]]:
        """Parse dependency files"""
        dependencies = {}
        
        # Python requirements.txt
        req_path = os.path.join(self.repo_path, 'requirements.txt')
        if os.path.exists(req_path):
            with open(req_path, 'r', encoding='utf-8', errors='ignore') as f:
                deps = f.read().strip().split('\n')
                dependencies["python"] = [d for d in deps if d and not d.startswith('#')]
        
        # Node package.json
        package_path = os.path.join(self.repo_path, 'package.json')
        if os.path.exists(package_path):
            with open(package_path, 'r') as f:
                try:
                    pkg = json.load(f)
                    all_deps = {}
                    all_deps.update(pkg.get('dependencies', {}))
                    all_deps.update(pkg.get('devDependencies', {}))
                    dependencies["node"] = [f"{k}@{v}" for k, v in all_deps.items()]
                except:
                    pass
        
        return dependencies
    
    def analyze_files(self) -> List[Dict]:
        """Analyze individual files"""
        files_info = []
        
        for root, dirs, files in os.walk(self.repo_path):
            if any(skip in root for skip in ['.git', '__pycache__', 'node_modules', 'venv', 'env']):
                continue
                
            for file in files:
                if file.endswith(('.py', '.js', '.jsx', '.ts', '.tsx', '.html', '.css')):
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, self.repo_path)
                    
                    # Get file size and line count
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = f.readlines()
                            line_count = len(lines)
                    except:
                        line_count = 0
                    
                    files_info.append({
                        "path": rel_path,
                        "type": os.path.splitext(file)[1],
                        "lines": line_count,
                        "size": os.path.getsize(file_path)
                    })
        
        return files_info
    
    def find_migration_opportunities(self) -> List[Dict]:
        """Find code that needs migration"""
        opportunities = []
        framework = self.analysis["framework"]
        
        if framework == "Django":
            # Check for deprecated Django features
            for file_info in self.analysis["files"]:
                if file_info["type"] == '.py':
                    file_path = os.path.join(self.repo_path, file_info["path"])
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        
                        # Check for url() patterns (Django 3.0+ uses path/re_path)
                        if 'url(' in content and 'path(' not in content:
                            opportunities.append({
                                "file": file_info["path"],
                                "type": "url_to_path",
                                "description": "Replace url() with path() or re_path()",
                                "severity": "medium"
                            })
                        
                        # Check for old middleware format
                        if 'MIDDLEWARE_CLASSES' in content:
                            opportunities.append({
                                "file": file_info["path"],
                                "type": "middleware_update",
                                "description": "Replace MIDDLEWARE_CLASSES with MIDDLEWARE",
                                "severity": "high"
                            })
        
        elif framework == "React":
            # Check for React 17 to 18 changes
            for file_info in self.analysis["files"]:
                if file_info["type"] in ['.js', '.jsx']:
                    file_path = os.path.join(self.repo_path, file_info["path"])
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        
                        # Check for ReactDOM.render (React 18 uses createRoot)
                        if 'ReactDOM.render' in content:
                            opportunities.append({
                                "file": file_info["path"],
                                "type": "reactdom_to_createroot",
                                "description": "Replace ReactDOM.render with createRoot",
                                "severity": "medium"
                            })
        
        return opportunities
    
    def calculate_stats(self) -> Dict:
        """Calculate repository statistics"""
        stats = {
            "total_files": len(self.analysis["files"]),
            "total_lines": 0,
            "python_files": 0,
            "js_files": 0,
            "html_files": 0,
            "css_files": 0
        }
        
        for file_info in self.analysis["files"]:
            stats["total_lines"] += file_info["lines"]
            
            if file_info["type"] == '.py':
                stats["python_files"] += 1
            elif file_info["type"] in ['.js', '.jsx', '.ts', '.tsx']:
                stats["js_files"] += 1
            elif file_info["type"] == '.html':
                stats["html_files"] += 1
            elif file_info["type"] == '.css':
                stats["css_files"] += 1
        
        return stats