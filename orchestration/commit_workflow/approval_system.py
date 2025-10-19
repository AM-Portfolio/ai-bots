"""
UI Approval System for GitHub commits and write operations
Ensures user confirms before executing destructive operations
"""

import logging
import uuid
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class ApprovalStatus(str, Enum):
    """Status of approval request"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


@dataclass
class ApprovalRequest:
    """
    Approval request for write operations
    Sent to UI for user confirmation before executing
    """
    id: str
    operation_type: str
    title: str
    description: str
    template_data: Dict[str, Any]
    status: ApprovalStatus
    created_at: datetime
    expires_at: datetime
    user_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "operation_type": self.operation_type,
            "title": self.title,
            "description": self.description,
            "template_data": self.template_data,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "user_id": self.user_id
        }


class ApprovalManager:
    """
    Manages approval requests for write operations
    Stores pending approvals and tracks their status
    """
    
    def __init__(self, expiration_minutes: int = 30):
        """
        Initialize approval manager
        
        Args:
            expiration_minutes: Minutes until approval request expires
        """
        self.pending_approvals: Dict[str, ApprovalRequest] = {}
        self.expiration_minutes = expiration_minutes
        logger.info(f"✅ Approval Manager initialized (expires in {expiration_minutes}min)")
    
    def create_approval_request(
        self,
        operation_type: str,
        title: str,
        description: str,
        template_data: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> ApprovalRequest:
        """
        Create new approval request
        
        Args:
            operation_type: Type of operation (github_commit, etc.)
            title: Request title
            description: Request description
            template_data: Template data for the operation
            user_id: Optional user ID
        
        Returns:
            ApprovalRequest object
        """
        request_id = str(uuid.uuid4())
        now = datetime.utcnow()
        expires_at = now + timedelta(minutes=self.expiration_minutes)
        
        approval_request = ApprovalRequest(
            id=request_id,
            operation_type=operation_type,
            title=title,
            description=description,
            template_data=template_data,
            status=ApprovalStatus.PENDING,
            created_at=now,
            expires_at=expires_at,
            user_id=user_id
        )
        
        self.pending_approvals[request_id] = approval_request
        
        logger.info(f"📋 Created approval request: {request_id} ({operation_type})")
        logger.info(f"   Title: {title}")
        logger.info(f"   Expires: {expires_at.isoformat()}")
        
        return approval_request
    
    def get_approval_request(self, request_id: str) -> Optional[ApprovalRequest]:
        """Get approval request by ID"""
        request = self.pending_approvals.get(request_id)
        
        if request and request.status == ApprovalStatus.PENDING:
            if datetime.utcnow() > request.expires_at:
                request.status = ApprovalStatus.EXPIRED
                logger.info(f"⏰ Approval request expired: {request_id}")
        
        return request
    
    def approve_request(
        self,
        request_id: str,
        updated_template_data: Optional[Dict[str, Any]] = None
    ) -> Optional[ApprovalRequest]:
        """
        Approve an approval request
        
        Args:
            request_id: Request ID
            updated_template_data: Optional updated template data from user
        
        Returns:
            Approved ApprovalRequest or None if not found/expired
        """
        request = self.get_approval_request(request_id)
        
        if not request:
            logger.warning(f"Approval request not found: {request_id}")
            return None
        
        if request.status == ApprovalStatus.EXPIRED:
            logger.warning(f"Cannot approve expired request: {request_id}")
            return None
        
        request.status = ApprovalStatus.APPROVED
        
        if updated_template_data:
            request.template_data.update(updated_template_data)
            logger.info(f"✏️ Updated template data for {request_id}")
        
        logger.info(f"✅ Approved request: {request_id}")
        
        return request
    
    def reject_request(self, request_id: str, reason: Optional[str] = None) -> bool:
        """
        Reject an approval request
        
        Args:
            request_id: Request ID
            reason: Optional rejection reason
        
        Returns:
            True if rejected, False if not found
        """
        request = self.get_approval_request(request_id)
        
        if not request:
            logger.warning(f"Approval request not found: {request_id}")
            return False
        
        request.status = ApprovalStatus.REJECTED
        logger.info(f"❌ Rejected request: {request_id}")
        if reason:
            logger.info(f"   Reason: {reason}")
        
        return True
    
    def list_pending_requests(self, user_id: Optional[str] = None) -> list[ApprovalRequest]:
        """
        List all pending approval requests
        
        Args:
            user_id: Optional filter by user ID
        
        Returns:
            List of pending ApprovalRequest objects
        """
        pending = []
        for request in self.pending_approvals.values():
            if request.status != ApprovalStatus.PENDING:
                continue
            
            if datetime.utcnow() > request.expires_at:
                request.status = ApprovalStatus.EXPIRED
                continue
            
            if user_id and request.user_id != user_id:
                continue
            
            pending.append(request)
        
        return pending
    
    def cleanup_expired_requests(self) -> int:
        """
        Clean up expired requests
        
        Returns:
            Number of requests cleaned up
        """
        now = datetime.utcnow()
        expired_ids = []
        
        for request_id, request in self.pending_approvals.items():
            if now > request.expires_at:
                expired_ids.append(request_id)
        
        for request_id in expired_ids:
            del self.pending_approvals[request_id]
        
        if expired_ids:
            logger.info(f"🧹 Cleaned up {len(expired_ids)} expired approval requests")
        
        return len(expired_ids)


_approval_manager: Optional[ApprovalManager] = None


def get_approval_manager() -> ApprovalManager:
    """Get global approval manager instance"""
    global _approval_manager
    if _approval_manager is None:
        _approval_manager = ApprovalManager()
    return _approval_manager
