# backend/routes/repositories.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import logging
import os
import uuid
import zipfile
import tempfile
from datetime import datetime

from backend.core.database import get_db
from backend.middleware.auth_middleware import get_current_user
from backend.models.user import User
from backend.models.repository import Repository
from backend.services.github_service import GitHubService

# ✅ Import all agents
from backend.agents import (
    MemorySystem,
    DiscoveryAgent,
    PlanningAgent,
    CodeMigrator,
    VerificationAgent,
    ReportAgent
)

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/")
async def get_repositories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        service = GitHubService(db)
        repos = await service.get_all_repositories(str(current_user.id))
        return repos
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/import")
async def import_repository(
    data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        service = GitHubService(db)
        result = await service.import_repository(
            user_id=str(current_user.id),
            repo_url=data.get("url"),
            branch=data.get("branch", "main")
        )
        return result
    except Exception as e:
        logger.error(f"Import error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/{repo_id}/download")
async def download_migrated_repo(
    repo_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Download the migrated repository as a ZIP file"""
    
    repo = db.query(Repository).filter(
        Repository.id == uuid.UUID(repo_id),
        Repository.user_id == current_user.id
    ).first()
    
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    clone_path = f"/tmp/migration_agent/repos/{current_user.id}/{repo.name}"
    
    if not os.path.exists(clone_path):
        raise HTTPException(status_code=404, detail="Repository not found on server")
    
    zip_path = tempfile.mktemp(suffix=".zip")
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(clone_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, clone_path)
                zipf.write(file_path, arcname)
    
    return FileResponse(
        path=zip_path,
        filename=f"{repo.name}_migrated.zip",
        media_type="application/zip"
    )

@router.post("/{repo_id}/analyze")
async def analyze_repository(
    repo_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        repo = db.query(Repository).filter(
            Repository.id == uuid.UUID(repo_id),
            Repository.user_id == current_user.id
        ).first()
        
        if not repo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Repository not found"
            )
        
        clone_path = f"/tmp/migration_agent/repos/{current_user.id}/{repo.name}"
        
        if not os.path.exists(clone_path):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Repository not cloned. Please import first."
            )
        
        memory = MemorySystem(str(repo_id))
        discovery = DiscoveryAgent(memory)
        result = await discovery.discover(clone_path)
        
        return result
        
    except Exception as e:
        logger.error(f"Analysis error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/{repo_id}/plan")
async def plan_migration(
    repo_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        repo = db.query(Repository).filter(
            Repository.id == uuid.UUID(repo_id),
            Repository.user_id == current_user.id
        ).first()
        
        if not repo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Repository not found"
            )
        
        clone_path = f"/tmp/migration_agent/repos/{current_user.id}/{repo.name}"
        
        if not os.path.exists(clone_path):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Repository not cloned. Please import first."
            )
        
        memory = MemorySystem(str(repo_id))
        discovery = DiscoveryAgent(memory)
        analysis = await discovery.discover(clone_path)
        
        planning = PlanningAgent(memory)
        plan = await planning.plan(analysis)
        
        return plan
        
    except Exception as e:
        logger.error(f"Planning error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/{repo_id}/migrate")
async def migrate_repository(
    repo_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        repo = db.query(Repository).filter(
            Repository.id == uuid.UUID(repo_id),
            Repository.user_id == current_user.id
        ).first()
        
        if not repo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Repository not found"
            )
        
        clone_path = f"/tmp/migration_agent/repos/{current_user.id}/{repo.name}"
        
        if not os.path.exists(clone_path):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Repository not cloned. Please import first."
            )
        
        memory = MemorySystem(str(repo_id))
        discovery = DiscoveryAgent(memory)
        analysis = await discovery.discover(clone_path)
        
        planning = PlanningAgent(memory)
        plan = await planning.plan(analysis)
        
        migrator = CodeMigrator(clone_path, plan)
        result = await migrator.execute()
        
        return result
        
    except Exception as e:
        logger.error(f"Migration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/{repo_id}/verify")
async def verify_repository(
    repo_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        repo = db.query(Repository).filter(
            Repository.id == uuid.UUID(repo_id),
            Repository.user_id == current_user.id
        ).first()
        
        if not repo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Repository not found"
            )
        
        clone_path = f"/tmp/migration_agent/repos/{current_user.id}/{repo.name}"
        
        if not os.path.exists(clone_path):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Repository not cloned. Please import first."
            )
        
        memory = MemorySystem(str(repo_id))
        verification = VerificationAgent(memory)
        result = await verification.verify(clone_path)
        
        return result
        
    except Exception as e:
        logger.error(f"Verification error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/{repo_id}/report")
async def generate_report(
    repo_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        repo = db.query(Repository).filter(
            Repository.id == uuid.UUID(repo_id),
            Repository.user_id == current_user.id
        ).first()
        
        if not repo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Repository not found"
            )
        
        clone_path = f"/tmp/migration_agent/repos/{current_user.id}/{repo.name}"
        
        if not os.path.exists(clone_path):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Repository not cloned. Please import first."
            )
        
        memory = MemorySystem(str(repo_id))
        discovery = DiscoveryAgent(memory)
        analysis = await discovery.discover(clone_path)

        planning = PlanningAgent(memory)
        plan = await planning.plan(analysis)

        migrator = CodeMigrator(clone_path, plan)
        migration_result = await migrator.execute()

        verification = VerificationAgent(memory)
        verification_result = await verification.verify(clone_path)

        report_agent = ReportAgent(memory)
        report = await report_agent.generate_report(clone_path)

        return report

    except Exception as e:
        logger.error(f"Report generation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/{repo_id}/download")
async def download_migrated_repo(
    repo_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Download the migrated repository as a ZIP file"""
    
    repo = db.query(Repository).filter(
        Repository.id == uuid.UUID(repo_id),
        Repository.user_id == current_user.id
    ).first()
    
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    clone_path = f"/tmp/migration_agent/repos/{current_user.id}/{repo.name}"
    
    if not os.path.exists(clone_path):
        raise HTTPException(status_code=404, detail="Repository not found on server")
    
    zip_path = tempfile.mktemp(suffix=".zip")
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(clone_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, clone_path)
                zipf.write(file_path, arcname)
    
    return FileResponse(
        path=zip_path,
        filename=f"{repo.name}_migrated.zip",
        media_type="application/zip"
    )
