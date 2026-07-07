from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import logging
import os
import uuid
from datetime import datetime

from backend.core.database import get_db
from backend.middleware.auth_middleware import get_current_user
from backend.models.user import User
from backend.models.repository import Repository
from backend.services.github_service import GitHubService

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/")
async def get_repositories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all repositories for the current user"""
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
    """Import a repository from GitHub"""
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

@router.post("/{repo_id}/analyze")
async def analyze_repository(
    repo_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Analyze a repository for migration opportunities"""
    try:
        from backend.agents.analyzer_agent import RepositoryAnalyzer
        
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
        
        analyzer = RepositoryAnalyzer(clone_path)
        analysis = await analyzer.analyze()
        
        repo.language = analysis.get("language")
        repo.framework = analysis.get("framework")
        repo.dependencies = analysis.get("dependencies", {})
        repo.file_count = analysis.get("stats", {}).get("total_files", 0)
        repo.last_analyzed = datetime.utcnow()
        db.commit()
        
        return analysis
        
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
    """Create a migration plan for a repository"""
    try:
        from backend.agents.analyzer_agent import RepositoryAnalyzer
        from backend.agents.planner_agent import MigrationPlanner
        
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
        
        analyzer = RepositoryAnalyzer(clone_path)
        analysis = await analyzer.analyze()
        
        planner = MigrationPlanner(analysis)
        plan = await planner.create_plan()
        
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
    """Execute migration on a repository"""
    try:
        from backend.agents.analyzer_agent import RepositoryAnalyzer
        from backend.agents.planner_agent import MigrationPlanner
        from backend.agents.migrator_agent import CodeMigrator
        
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
        
        analyzer = RepositoryAnalyzer(clone_path)
        analysis = await analyzer.analyze()
        
        planner = MigrationPlanner(analysis)
        plan = await planner.create_plan()
        
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
    """Verify a repository by running tests"""
    try:
        from backend.agents.verification_agent import VerificationAgent
        
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
        
        verifier = VerificationAgent(clone_path)
        results = await verifier.verify()
        
        return results
        
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
    """Generate migration report for a repository"""
    try:
        from backend.agents.analyzer_agent import RepositoryAnalyzer
        from backend.agents.planner_agent import MigrationPlanner
        from backend.agents.migrator_agent import CodeMigrator
        from backend.agents.verification_agent import VerificationAgent
        from backend.agents.report_agent import ReportAgent
        
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
        
        # Analyze
        analyzer = RepositoryAnalyzer(clone_path)
        analysis = await analyzer.analyze()
        
        # Create plan
        planner = MigrationPlanner(analysis)
        plan = await planner.create_plan()
        
        # Execute migration
        migrator = CodeMigrator(clone_path, plan)
        migration_result = await migrator.execute()
        
        # Verify
        verifier = VerificationAgent(clone_path)
        verification_result = await verifier.verify()
        
        # Generate report
        report_agent = ReportAgent(clone_path, analysis, plan, migration_result, verification_result)
        report = await report_agent.generate_report()
        
        return report
        
    except Exception as e:
        logger.error(f"Report generation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    
@router.post("/{repo_id}/docker-migrate")
async def docker_migrate(
    repo_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Execute migration using Docker sandbox"""
    try:
        from backend.agents.analyzer_agent import RepositoryAnalyzer
        from backend.agents.planner_agent import MigrationPlanner
        from backend.agents.migrator_agent import CodeMigrator
        
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
        
        # Analyze
        analyzer = RepositoryAnalyzer(clone_path)
        analysis = await analyzer.analyze()
        
        # Create plan
        planner = MigrationPlanner(analysis)
        plan = await planner.create_plan()
        
        # Execute migration with Docker
        migrator = CodeMigrator(clone_path, plan)
        result = await migrator.execute_with_docker()
        
        return result
        
    except Exception as e:
        logger.error(f"Docker migration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )