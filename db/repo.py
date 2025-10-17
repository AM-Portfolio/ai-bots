from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from .models import Issue, Analysis, Fix


class IssueRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, external_id: str, title: str, description: str, source: str, **kwargs) -> Issue:
        issue = Issue(
            external_id=external_id,
            title=title,
            description=description,
            source=source,
            **kwargs
        )
        self.db.add(issue)
        self.db.commit()
        self.db.refresh(issue)
        return issue
    
    def get_by_external_id(self, external_id: str) -> Optional[Issue]:
        return self.db.query(Issue).filter(Issue.external_id == external_id).first()
    
    def get_by_id(self, issue_id: int) -> Optional[Issue]:
        return self.db.query(Issue).filter(Issue.id == issue_id).first()
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[Issue]:
        return self.db.query(Issue).offset(skip).limit(limit).all()
    
    def update_status(self, issue_id: int, status: str) -> bool:
        issue = self.get_by_id(issue_id)
        if issue:
            issue.status = status
            issue.updated_at = datetime.utcnow()
            self.db.commit()
            return True
        return False


class AnalysisRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def create(
        self,
        issue_id: int,
        root_cause: str,
        confidence_score: float,
        **kwargs
    ) -> Analysis:
        analysis = Analysis(
            issue_id=issue_id,
            root_cause=root_cause,
            confidence_score=confidence_score,
            **kwargs
        )
        self.db.add(analysis)
        self.db.commit()
        self.db.refresh(analysis)
        return analysis
    
    def get_by_issue(self, issue_id: int) -> List[Analysis]:
        return self.db.query(Analysis).filter(Analysis.issue_id == issue_id).all()
    
    def add_fix(
        self,
        analysis_id: int,
        file_path: str,
        original_code: str,
        fixed_code: str,
        explanation: str,
        **kwargs
    ) -> Fix:
        fix = Fix(
            analysis_id=analysis_id,
            file_path=file_path,
            original_code=original_code,
            fixed_code=fixed_code,
            explanation=explanation,
            **kwargs
        )
        self.db.add(fix)
        self.db.commit()
        self.db.refresh(fix)
        return fix
