import os, git, shutil, json, hashlib, logging
from typing import Dict, List
from datetime import datetime
from github import Github
from sqlalchemy.orm import Session
import uuid
from backend.models.repository import Repository

logger = logging.getLogger(__name__)

class GitHubService:
    def __init__(self, db: Session, access_token: str = None):
        self.db = db
        self.client = Github(access_token) if access_token else None
        self.repo_path = "/tmp/migration_agent/repos"
        os.makedirs(self.repo_path, exist_ok=True)
    
    async def import_repository(self, user_id: str, repo_url: str, branch: str = None) -> Dict:
        try:
            full_name = repo_url.replace("https://github.com/", "").replace(".git", "")
            repo_name = full_name.split("/")[-1]
            
            existing = self.db.query(Repository).filter(
                Repository.full_name == full_name,
                Repository.user_id == uuid.UUID(user_id)
            ).first()
            if existing:
                return {"message": "Already imported", "id": str(existing.id)}
            
            clone_path = os.path.join(self.repo_path, user_id, repo_name)
            if os.path.exists(clone_path):
                shutil.rmtree(clone_path)
            
            if branch:
                try:
                    git.Repo.clone_from(repo_url, clone_path, branch=branch)
                except git.exc.GitCommandError as e:
                    if "Remote branch" in str(e) and "not found" in str(e):
                        logger.warning(f"Branch '{branch}' not found, falling back to default branch.")
                        if os.path.exists(clone_path):
                            shutil.rmtree(clone_path)
                        git.Repo.clone_from(repo_url, clone_path)
                    else:
                        raise
            else:
                git.Repo.clone_from(repo_url, clone_path)
            
            github_id = int(hashlib.md5(full_name.encode()).hexdigest()[:8], 16)
            
            repo = Repository(
                user_id=uuid.UUID(user_id),
                github_id=github_id,
                name=repo_name,
                full_name=full_name,
                clone_url=repo_url,
                html_url=f"https://github.com/{full_name}",
                is_imported=True,
                file_count=1
            )
            self.db.add(repo)
            self.db.commit()
            self.db.refresh(repo)
            
            return {"id": str(repo.id), "name": repo.name, "full_name": repo.full_name}
        except Exception as e:
            raise ValueError(f"Import failed: {str(e)}")
    
    async def get_all_repositories(self, user_id: str) -> List[Dict]:
        repos = self.db.query(Repository).filter(
            Repository.user_id == uuid.UUID(user_id)
        ).all()
        return [{"id": str(r.id), "name": r.name, "full_name": r.full_name, "status": "Ready"} for r in repos]
