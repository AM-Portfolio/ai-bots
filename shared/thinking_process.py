"""
Shared thinking process model for backend flow visibility.
Provides step-by-step tracking of AI processing workflows.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class StepStatus(Enum):
    """Status of a thinking process step"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class ThinkingStep:
    """Individual step in the thinking process"""
    id: str
    title: str
    description: str
    status: StepStatus = StepStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "metadata": self.metadata,
            "error": self.error,
            "duration_ms": self._get_duration_ms()
        }
    
    def _get_duration_ms(self) -> Optional[int]:
        """Calculate duration in milliseconds"""
        if self.start_time and self.end_time:
            delta = self.end_time - self.start_time
            return int(delta.total_seconds() * 1000)
        return None


@dataclass
class ThinkingProcess:
    """Complete thinking process with ordered steps"""
    workflow_id: str
    workflow_type: str  # 'llm_test', 'doc_orchestrator', etc.
    steps: List[ThinkingStep] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    
    def add_step(self, step_id: str, title: str, description: str) -> ThinkingStep:
        """Add a new step to the process"""
        step = ThinkingStep(
            id=step_id,
            title=title,
            description=description,
            status=StepStatus.PENDING
        )
        self.steps.append(step)
        return step
    
    def start_step(self, step_id: str) -> Optional[ThinkingStep]:
        """Mark a step as in progress"""
        step = self._find_step(step_id)
        if step:
            step.status = StepStatus.IN_PROGRESS
            step.start_time = datetime.now()
        return step
    
    def complete_step(self, step_id: str, metadata: Optional[Dict[str, Any]] = None) -> Optional[ThinkingStep]:
        """Mark a step as completed"""
        step = self._find_step(step_id)
        if step:
            step.status = StepStatus.COMPLETED
            step.end_time = datetime.now()
            if metadata:
                step.metadata.update(metadata)
        return step
    
    def fail_step(self, step_id: str, error: str) -> Optional[ThinkingStep]:
        """Mark a step as failed"""
        step = self._find_step(step_id)
        if step:
            step.status = StepStatus.FAILED
            step.end_time = datetime.now()
            step.error = error
        return step
    
    def skip_step(self, step_id: str, reason: str) -> Optional[ThinkingStep]:
        """Mark a step as skipped"""
        step = self._find_step(step_id)
        if step:
            step.status = StepStatus.SKIPPED
            step.end_time = datetime.now()
            step.metadata["skip_reason"] = reason
        return step
    
    def _find_step(self, step_id: str) -> Optional[ThinkingStep]:
        """Find a step by ID"""
        for step in self.steps:
            if step.id == step_id:
                return step
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "workflow_id": self.workflow_id,
            "workflow_type": self.workflow_type,
            "steps": [step.to_dict() for step in self.steps],
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "total_duration_ms": self._get_total_duration_ms(),
            "status": self._get_overall_status()
        }
    
    def _get_total_duration_ms(self) -> Optional[int]:
        """Calculate total duration in milliseconds"""
        if self.end_time:
            delta = self.end_time - self.start_time
            return int(delta.total_seconds() * 1000)
        return None
    
    def _get_overall_status(self) -> str:
        """Get overall status based on step statuses"""
        if any(step.status == StepStatus.FAILED for step in self.steps):
            return "failed"
        if any(step.status == StepStatus.IN_PROGRESS for step in self.steps):
            return "in_progress"
        if all(step.status in [StepStatus.COMPLETED, StepStatus.SKIPPED] for step in self.steps):
            return "completed"
        return "pending"


def create_llm_thinking_process(workflow_id: str) -> ThinkingProcess:
    """Create a thinking process for LLM testing"""
    process = ThinkingProcess(workflow_id=workflow_id, workflow_type="llm_test")
    
    # Define standard LLM workflow steps
    process.add_step("validate_input", "Validate Input", "Checking user input and parameters")
    process.add_step("check_github", "Check GitHub Context", "Detecting GitHub repository mentions")
    process.add_step("select_provider", "Select LLM Provider", "Choosing AI provider (Together AI / Azure OpenAI)")
    process.add_step("prepare_prompt", "Prepare Prompt", "Formatting prompt with context")
    process.add_step("call_llm", "Call LLM", "Sending request to AI provider")
    process.add_step("process_response", "Process Response", "Parsing and formatting AI response")
    
    return process


def create_doc_orchestrator_thinking_process(workflow_id: str) -> ThinkingProcess:
    """Create a thinking process for documentation orchestrator"""
    process = ThinkingProcess(workflow_id=workflow_id, workflow_type="doc_orchestrator")
    
    # Define standard doc orchestrator workflow steps
    process.add_step("validate_repo", "Validate Repository", "Checking GitHub repository access")
    process.add_step("analyze_code", "Analyze Code", "AI analyzing repository code")
    process.add_step("generate_docs", "Generate Documentation", "AI generating documentation content")
    process.add_step("create_commit", "Create Commit", "Preparing documentation files for commit")
    process.add_step("push_to_github", "Push to GitHub", "Committing documentation to repository")
    process.add_step("publish_confluence", "Publish to Confluence", "Publishing documentation to Confluence")
    
    return process
