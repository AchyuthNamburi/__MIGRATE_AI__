# backend/tools/sechub_tool.py
"""SecHub - Security scanning for migrated code"""

import subprocess
import json
import os
from typing import Dict, List, Optional


class SecHubTool:
    """
    SecHub performs security scanning on code
    Detects vulnerabilities, secrets, and license issues
    """
    
    def __init__(self, local_mode: bool = True):
        self.local_mode = local_mode
        self.scans_performed = 0
        self.findings = []
    
    async def scan_code(self, repo_path: str) -> Dict:
        """Run a security scan on the repository"""
        self.scans_performed += 1
        
        if self.local_mode:
            return self._local_scan(repo_path)
        else:
            return await self._api_scan(repo_path)
    
    def _local_scan(self, repo_path: str) -> Dict:
        """Run local security scan using available tools"""
        results = {
            "vulnerabilities": [],
            "secrets": [],
            "license_issues": [],
            "summary": {
                "total_findings": 0,
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0
            }
        }
        
        # 1. Check for hardcoded secrets
        secrets = self._scan_for_secrets(repo_path)
        results["secrets"] = secrets
        results["summary"]["total_findings"] += len(secrets)
        
        # 2. Check for known vulnerable patterns
        vulnerabilities = self._scan_for_vulnerabilities(repo_path)
        results["vulnerabilities"] = vulnerabilities
        results["summary"]["total_findings"] += len(vulnerabilities)
        
        # 3. Check for license issues
        license_issues = self._scan_for_licenses(repo_path)
        results["license_issues"] = license_issues
        results["summary"]["total_findings"] += len(license_issues)
        
        # Store findings
        self.findings.extend(results["vulnerabilities"])
        self.findings.extend(results["secrets"])
        
        return results
    
    def _scan_for_secrets(self, repo_path: str) -> List[Dict]:
        """Scan for hardcoded secrets (API keys, passwords, etc.)"""
        secrets = []
        patterns = [
            ("API_KEY", r'API_KEY\s*=\s*["\']([^"\']+)["\']'),
            ("SECRET_KEY", r'SECRET_KEY\s*=\s*["\']([^"\']+)["\']'),
            ("PASSWORD", r'PASSWORD\s*=\s*["\']([^"\']+)["\']'),
            ("TOKEN", r'TOKEN\s*=\s*["\']([^"\']+)["\']')
        ]
        
        for root, dirs, files in os.walk(repo_path):
            # Skip common directories
            if any(skip in root for skip in ['.git', '__pycache__', 'node_modules', 'venv']):
                continue
            
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        for secret_type, pattern in patterns:
                            import re
                            matches = re.findall(pattern, content)
                            for match in matches:
                                # Don't report placeholder values
                                if match and len(match) > 4 and 'your_' not in match.lower() and 'example' not in match.lower():
                                    secrets.append({
                                        "type": secret_type,
                                        "file": os.path.relpath(file_path, repo_path),
                                        "severity": "HIGH",
                                        "message": f"Hardcoded {secret_type} found"
                                    })
                except:
                    pass
        
        return secrets
    
    def _scan_for_vulnerabilities(self, repo_path: str) -> List[Dict]:
        """Scan for known vulnerable patterns"""
        vulnerabilities = []
        
        # Check for known vulnerable patterns
        patterns = [
            ("eval", r'[^a-zA-Z]eval\s*\(', "Use of eval() is dangerous"),
            ("exec", r'[^a-zA-Z]exec\s*\(', "Use of exec() is dangerous"),
            ("input", r'input\s*\(', "Use of input() without validation")
        ]
        
        for root, dirs, files in os.walk(repo_path):
            if any(skip in root for skip in ['.git', '__pycache__', 'node_modules', 'venv']):
                continue
            
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            for vuln_type, pattern, message in patterns:
                                import re
                                if re.search(pattern, content):
                                    vulnerabilities.append({
                                        "type": vuln_type,
                                        "file": os.path.relpath(file_path, repo_path),
                                        "severity": "MEDIUM",
                                        "message": message
                                    })
                    except:
                        pass
        
        return vulnerabilities
    
    def _scan_for_licenses(self, repo_path: str) -> List[Dict]:
        """Scan for license issues"""
        # Simple check for missing LICENSE file
        if not os.path.exists(os.path.join(repo_path, 'LICENSE')):
            return [{
                "type": "LICENSE_MISSING",
                "file": "LICENSE",
                "severity": "LOW",
                "message": "No LICENSE file found"
            }]
        return []
    
    async def _api_scan(self, repo_path: str) -> Dict:
        """Run scan via SecHub API (if you have a SecHub server)"""
        # This would use the SecHub API if available
        # For now, fall back to local scan
        return self._local_scan(repo_path)
    
    def get_report(self) -> Dict:
        """Get a summary report of all scans"""
        return {
            "total_scans": self.scans_performed,
            "total_findings": len(self.findings),
            "findings": self.findings
        }