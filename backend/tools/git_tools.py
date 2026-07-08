# backend/tools/git_tools.py
"""Git operations tools"""

import os
import git
import shutil
from typing import Optional, Dict


class GitTools:
    """Git operations for the migration agent"""
    
    def __init__(self):
        self.repo = None
        self.repo_path = None
    
    def clone(self, url: str, path: str, branch: str = "main") -> Dict:
        """Clone a repository"""
        try:
            # Remove existing directory if it exists
            if os.path.exists(path):
                shutil.rmtree(path)
            
            self.repo = git.Repo.clone_from(url, path, branch=branch)
            self.repo_path = path
            
            return {
                "success": True,
                "path": path,
                "branch": branch,
                "url": url
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def diff(self, repo_path: Optional[str] = None) -> str:
        """Get the current diff"""
        if repo_path:
            repo = git.Repo(repo_path)
        else:
            repo = self.repo
        
        if not repo:
            return ""
        
        return repo.git.diff()
    
    def get_branch(self, repo_path: Optional[str] = None) -> str:
        """Get the current branch"""
        if repo_path:
            repo = git.Repo(repo_path)
        else:
            repo = self.repo
        
        if not repo:
            return ""
        
        return repo.active_branch.name
    
    def commit(self, message: str, repo_path: Optional[str] = None) -> Dict:
        """Commit changes"""
        if repo_path:
            repo = git.Repo(repo_path)
        else:
            repo = self.repo
        
        if not repo:
            return {"success": False, "error": "No repository found"}
        
        try:
            repo.git.add(A=True)
            repo.index.commit(message)
            return {"success": True, "message": message}
        except Exception as e:
            return {"success": False, "error": str(e)}